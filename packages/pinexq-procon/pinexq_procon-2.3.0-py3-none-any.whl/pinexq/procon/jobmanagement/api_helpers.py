import logging
import os
import warnings
from enum import StrEnum
from typing import Any

import httpx
import jwt
from httpx_caching import CachingClient
from pinexq.client.job_management import Job, enter_jma
from pinexq.client.job_management.hcos import EntryPointHco

from ..core.exceptions import ProConException
from ..runtime.job import RemoteExecutionContext
from ..step import Step
from ..step.step import ExecutionContextType


logger = logging.getLogger(__name__)


class JmaApiHeaders(StrEnum):
    api_key = "x-api-key"
    access_token = "x-access-token"


PREFIX = "JMC_"
API_HOST_URL = f"{PREFIX}API_HOST_URL"
API_KEY = f"{PREFIX}API_KEY"
ACCESS_TOKEN = f"{PREFIX}ACCESS_TOKEN"

# use a client with local cache
USE_CLIENT_WITH_CACHE = True

# Environment variables that will directly translate to HTTP headers
#  'header-name': 'ENVIRONMENT_VARIABLE'
HEADERS_FROM_ENV = {
    JmaApiHeaders.api_key: API_KEY,
    JmaApiHeaders.access_token: ACCESS_TOKEN,
}

def _create_client_instance(api_endpoint: str, headers: dict) -> httpx.Client:
    """
    Will create a httpx client, optional with caching, to be used with the API objects.

    Args:
        api_endpoint: The endpoint for the pinexq API.
        headers: headers to be passed to httpx.Client.

    """
    client =  httpx.Client(base_url=api_endpoint, headers=headers)
    if USE_CLIENT_WITH_CACHE:
        # for now, we use the persistent cache, which is also shared between instances
        # use  if you need each client to have a own cache storage=InMemoryStorage()
        # broken, will cache SSE stream
        #return SyncCacheClient(
        #    base_url=pinexq_api_endpoint,
        #    headers=headers,
        #    timeout=timeout)
        return CachingClient(client)
    else:
        return client

def client_from_env_vars() -> httpx.Client:
    """Initializes a httpx.Client from environment variables.

    The following variables are used:
        JMC_API_KEY: (header, optional) The api-key you get from the login portal.
        JMC_ACCESS_TOKEN: (header, optional) The JWT access token for the JM.
    """
    try:
        api_url = os.environ[API_HOST_URL]
    except KeyError:
        raise ProConException(
            f'Environment variable "{API_HOST_URL}" not found!'
            f" Can not configure job management api access!"
        )
    headers = {hdr: os.environ[env] for hdr, env in HEADERS_FROM_ENV.items() if env in os.environ}
    return _create_client_instance(api_endpoint=api_url, headers=headers)


def client_from_job_execution_context(exec_context: ExecutionContextType) -> httpx.Client:
    # This function will be deprecated and replaced by the function below!
    """Initializes a httpx.Client from connection info embedded in the job.offer.

    Tries to get the JMApi-host and headers from the environment variables first.
    If not available, the host is extracted from the job-url in the job.offer. Headers
    are set by the information provided job.offer.
    """

    warnings.warn(
        "Calling `client_from_job_execution_context()` directly will be deprecated "
        "in future releases. Please use the equivalent `get_client()` function instead.",
        DeprecationWarning
    )

    if not exec_context.current_job_offer:
        raise ProConException(
            "Current execution context provides no information to create client (no job offer)."
        )

    job_context = exec_context.current_job_offer.job_execution_context

    try:
        # fixme: Redundant, as there is an explicit get_from_env_vars function
        api_url = os.environ[API_HOST_URL]
    except KeyError:
        # Return only the host-url, cutoff path and query
        api_url = httpx.URL(job_context.job_url).join("/")

    # Create header from environment variables
    # fixme: Redundant, as there is an explicit get_from_env_vars function
    env_var_headers = {
        hdr: os.environ[env] for hdr, env in HEADERS_FROM_ENV.items() if env in os.environ
    }
    # Create headers from the settings in the job.offer
    if job_context.access_token is not None:
        job_offer_headers = {
            JmaApiHeaders.access_token.value: job_context.access_token,
        }
    else:
        job_offer_headers = {}

    # Update headers from env-vars with info from the job.offer
    headers = env_var_headers | job_offer_headers
    return _create_client_instance(api_endpoint=api_url, headers=headers)


def _client_from_job_execution_context(context: ExecutionContextType) -> httpx.Client:
    # This function will replace the deprecated one above!
    """Initializes a httpx.Client from connection info embedded in the job.offer.

    The host is extracted from the job-url in the job.offer. Headers are set by the
    information provided job.offer.
    """
    if not context.current_job_offer:
        raise ProConException(
            "Current execution context provides no information to create client (no job offer)."
        )

    job_context = context.current_job_offer.job_execution_context

    # Return only the host-url, cutoff path and query
    api_url = httpx.URL(job_context.job_url).join("/")

    # Create headers from the settings in the job.offer
    job_offer_headers = {}
    if job_context.access_token:
        job_offer_headers[JmaApiHeaders.access_token.value] = job_context.access_token

    # Update headers from env-vars with info from the job.offer
    return _create_client_instance(api_endpoint=str(api_url), headers=job_offer_headers)


def get_client(context: ExecutionContextType | None = None) -> httpx.Client:
    """Trys to get the client fom job offer context if exec_context is provided.
    If not possible it trys to get it from environment variables (intended for testing).

    Args:
        context: The execution context of the current Step container.

    Returns:
        An initialized HTTPX client with base_url and headers set.

    Raises:
        ...
    """

    if context:
        try:
            return _client_from_job_execution_context(context)
        except ProConException as ex:
            logger.warning(
                f"Unable to initialize client from execution context: {str(ex)}. "
                f"Falling back to configure client from environment variables."
            )
    try:
        return client_from_env_vars()
    except ProConException as ex:
        raise ProConException(
            "Unable to determine API host and credentials from neither execution "
            "context (if running as 'remote') or environment variables!"
        ) from ex


def _job_from_context(context: ExecutionContextType, client: httpx.Client) -> Job:
    """Create a PinexQ client `Job` object from a given step-function's
    execution context and a httpx client.

    Args:
        context: The execution context of the current Step container.

    Returns:
        An initialized HTTPX client with base_url and headers set.
    """
    job_url = httpx.URL(context.current_job_offer.job_execution_context.job_url)
    return Job.from_url(client=client, job_url=job_url)


def job_from_step_context(step: Step, client: httpx.Client | None = None) -> Job:
    """Initialize an API Job object with the job_id of the current Job.

    Meant to be called inside a Step-container during execution of a Step-function.

    Args:
        step: The current Step container (referenced by `self`)
        client: A httpx.Client initialized with the API-url.
    """
    # Todo: Mark this function deprecated and refer to `get_job()` instead?
    context: RemoteExecutionContext | None = step.step_context
    if not client:
        client = get_client(context)

    return _job_from_context(context, client)


def get_job(context: ExecutionContextType) -> Job:
    """Create a PinexQ client `Job` object from a step-function's execution context.

    Args:
        context: The execution context of the current Step container.
    Returns:
        A pinexq.client.job_management.tool.Job object initialized as the Job executing the given context.
    """
    client = get_client(context)
    return _job_from_context(context, client)


def get_entrypoint_hco(context: ExecutionContextType) -> EntryPointHco:
    """Create a PinexQ client `Entrypoint` object from a step-function's execution context.

    Args:
        context: The execution context of the current Step container.
    Returns:
        An entrypoint hco object to the JMA where the current Job is running.
    """
    client = get_client(context)
    return enter_jma(client)


def get_grants(context: ExecutionContextType) -> list[str]:
    """Try to access grants for the current user

    Args:
        context: Execution context of the current step function
    Returns:
        A list of grants that could be determined or an empty list.
    """
    access_token = _get_access_token(context)
    if (access_token is None) or (access_token.get("grants") is None):
        return []

    try:
        grants = access_token["grants"]
        return grants
    except Exception as ex:
        raise ProConException("Can not extract Grants from access token.") from ex


def _get_access_token(context: ExecutionContextType) -> Any | None:
    """Trys to get access token. If one is contained in the job offer it is taken.
    else it trys to get an AccessToken from the environment variables.

    Args:
        context: Execution context of the current step function
    Returns:
        A access token raw string or None.
    """

    access_token: str | None = None
    try:
        # This will fail, if we're not in a RemoteExecutionContext, there's no job offer or no token
        access_token = context.current_job_offer.job_execution_context.access_token
    except AttributeError:
        pass

    # Fall back to environment variables, if the previous step failed
    access_token = access_token or os.environ.get(HEADERS_FROM_ENV[JmaApiHeaders.access_token])

    if access_token is None:
        return None

    try:
        token_content = jwt.decode(access_token, options={"verify_signature": False})
        return token_content
    except jwt.InvalidTokenError as ex:
        raise ProConException("Access token could not be decoded!") from ex
