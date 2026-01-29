"""
This is the CLI interface for the module.
It provides the entry points and top-level implementation for all commands.

The available commands are:
<your_script.py>
    - list: List the available functions
    - run: Execute a function locally
    - signature: Show a functions signature
    - remote: Connect to job-management remotely
    - register: Register a functions signature via the API
"""

import ast
import json
import logging
import uuid
from typing import Any

import click
import rich
from pydantic import BaseModel

from ..dataslots import create_dataslot_description
from ..step import Step
from ..step.step import ExecutionContext
from .exceptions import ProConUnknownFunctionError
from .helpers import log_version_info, remove_environment_variables
from .logconfig import configure_logging
from .naming import is_valid_version_string


logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """CLI interface for the processing container."""
    # The Step object is provided as *obj* when invoking *cli* in Step.__init__()
    #  and available in the context *ctx* to all subcommands.
    step: Step = ctx.obj  # noqa: F841  # here it is just for demonstration


@cli.command(name="list")  # avoid shadowing builtin 'list'
@click.option("-j", "--json", "json_", is_flag=True, help="Output in JSON format")
@click.option("-y", "--pretty", is_flag=True, help="Prettier output with color and comments")
@click.pass_context
def list_(ctx, json_: bool, pretty: bool):
    """List all available functions in this container."""
    step: Step = ctx.obj
    # noinspection PyProtectedMember
    funcs = step._signatures.items()

    if json_:
        func_names = [name for name, _ in funcs]
        print(json.dumps(func_names))
        return

    if pretty:
        rich.print("\nAvailable functions:")
        for name, schema in funcs:
            short_doc = f"# {schema.signature['short_description']}"
            rich.print(f"[green]{name:<16}[/green]  {short_doc}")
    else:
        for name, _ in funcs:
            rich.print(f"{name}")


@cli.command()
@click.option("-f", "--function", type=str, required=True, help="The function to be called in this container.")
@click.option("-p", "--parameters", help="Parameters formatted as Python dictionary")
@click.option("-di", "--input-dataslots", help="URIs for input dataslots formatted as Python dictionary")
@click.option("-do", "--output-dataslots", help="URIs for output dataslots formatted as Python dictionary")
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, dir_okay=False),
    help="Json-formatted file with function parameters",
)
@click.option("-o", "--output-file", type=click.Path(exists=False, dir_okay=False), help="Output file (Json-formatted)")
@click.option("-j", "--json", "as_json", is_flag=True, help="Output as JSON schema")
@click.option("-y", "--pretty", is_flag=True, help="Format output indentations and color")
@click.option("-d", "--debug", is_flag=True, help="enable more verbose debug output")
@click.option("-r", "--richformat", is_flag=True, help="enable rich formatting of log output")
@click.pass_context
def run(
    ctx,
    function: str,
    parameters: str,
    input_dataslots: str,
    output_dataslots: str,
    input_file: click.Path,
    output_file: click.Path,
    as_json: bool,
    pretty: bool,
    debug: bool = False,
    richformat: bool = False,
):
    """Execute a function locally.

    You can provide the PARAMETERS for the FUNCTION as a Python dictionary:
    e.g. python <this_script> -f <function_name> -p "{'a':1, 'b':'Hello'}"

    Dataslots can be defined the same way as parameters for local testing:
    e.g. python <this_script> -f <function_name> -di "{'slot_name':'/usr/test/data.txt'}"

    Alternatively you can read the parameters from a Json-formatted INPUT-FILE.

    The result is written to the console or to a Json-formatted OUTPUT-FILE.
    """
    from pinexq.procon.dataslots.metadata import LocalFileMetadataStore

    configure_logging(debug=debug, rich=richformat)
    log_version_info(log=True)

    step: Step = ctx.obj

    # noinspection PyProtectedMember
    if function not in step._signatures:
        exit_unknown_function(step, function)

    if parameters and input_file:
        raise ValueError("Parameters provided by commandline and file. Use either of those options.")

    func_params = {}  # Default - a function might not need parameters
    if parameters:
        func_params = params_from_python_expr(parameters)
    if input_file:
        func_params = params_from_json_file(str(input_file))
    input_dataslot_params = {}
    output_dataslot_params = {}
    if input_dataslots:
        raw_dataslot_parameters = params_from_python_expr(input_dataslots)
        input_dataslot_params = create_dataslot_description(raw_dataslot_parameters)
    if output_dataslots:
        raw_dataslot_parameters = params_from_python_expr(output_dataslots)
        output_dataslot_params = create_dataslot_description(raw_dataslot_parameters)

    metadata_handler = LocalFileMetadataStore()

    context = ExecutionContext(
        function_name=function,
        parameters=func_params,
        input_dataslots=input_dataslot_params,
        output_dataslots=output_dataslot_params,
        metadata_handler=metadata_handler,
    )
    # noinspection PyProtectedMember
    result = step._call(context)

    print_to_console(result, as_json, pretty)

    if output_file:
        write_to_json_file(str(output_file), result)


@cli.command()
@click.option("-j", "--json", "as_json", is_flag=True, help="Output as JSON schema")
@click.option("-y", "--pretty", is_flag=True, help="Format JSON with indentations and color")
@click.option("-f", "--function", type=str, help="The function to be inspected in this container.")
@click.pass_context
def signature(ctx, function: str, as_json: bool, pretty: bool):
    """Output a functions signature"""
    step: Step = ctx.obj

    # noinspection PyProtectedMember
    if function not in step._signatures:
        exit_unknown_function(step, function)

    # noinspection PyProtectedMember
    schema = step._signatures[function]
    model = schema.get_function_model()
    if as_json:
        if pretty:
            rich.print_json(model.model_dump_json(by_alias=True))
        else:
            print(model.model_dump_json(by_alias=True))
    else:
        rich.print(model)


def exit_unknown_function(step: Step, func_name: str):
    """Raises a custom `click` exception, in case an unknown Step-function name was provided."""
    # noinspection PyProtectedMember
    available_funcs = ", ".join((f"'{func}'" for func in step._signatures.keys()))
    raise click.BadParameter(
        f"No definition found for: '{func_name}'! Available functions: {available_funcs}", param_hint="function"
    )


def print_to_console(result: object, as_json: bool, pretty: bool):
    """Prints the Repr of a given object to StdOut. Optionally output the JSON representation
    of the object and/or use `rich` for a nicer output.

    Args:
        result: The object whose __repr__ to print.
        as_json: Format the output as Json if True.
        pretty: Use `rich` for printing, if True.
    """
    if as_json:
        result = result.model_dump_json() if isinstance(result, BaseModel) else result
        output = json.dumps(result)
    else:
        output = result

    if pretty:
        if as_json:
            rich.print_json(output)
        else:
            rich.print(output)
    else:
        print(output)


def params_from_python_expr(expr: str) -> dict[str, Any]:
    """Parses a string of a Python expression into its object representation."""
    params = ast.literal_eval(expr)
    if not isinstance(params, dict):
        raise ValueError("Parameters are not formatted as a Python dictionary!")
    return params


def params_from_json_file(filename: str) -> dict:
    """Loads data from a Json file into a dictionary."""
    with open(filename) as f:
        params = json.load(f)
    if not isinstance(params, dict):
        raise ValueError("Parameter file is not formatted as a Python dictionary!")
    return params


def write_to_json_file(filename: str, data: object):
    """Writes the Json representation of an object into a Json file."""
    with open(str(filename), "w") as f:
        data = data.model_dump_json() if isinstance(data, BaseModel) else data
        return json.dump(data, f)


@cli.command()
@click.option("--host", type=str, required=True, help="RabbitMQ host")
@click.option("--port", type=int, default=5671, required=True, help="RabbitMQ port")
@click.option("--apikey", type=str, help="RabbitMQ API-Key (used instead of user/pw)")
@click.option("--user", type=str, help="RabbitMQ user name")
@click.option("--password", type=str, help="RabbitMQ password")
@click.option("--exchange", type=str, default="processing-topic-exchange", help="RabbitMQ exchange name")
@click.option("--vhost", type=str, default="/", help="RabbitMQ virtual host")
@click.option("-d", "--debug", is_flag=True, help="enable more verbose debug output")
@click.option("-r", "--richformat", is_flag=True, help="enable rich formatting of log output")
@click.option("-f", "--function", type=str, multiple=True, help="The function(s) to be exposed to the job-management.")
@click.option("-af", "--allfunctions", is_flag=True, help="Expose all available functions")
@click.option(
    "-v", "--version", type=str, default="0", help="The version of all function(s) registered by this container (deprecated)"
)
@click.option("--workerid", type=str, default=uuid.uuid4(), help="Set a worker id (default: random uuid)")
@click.option("--contextid", type=str, required=True, help="The context-id this worker will be running in")
@click.option("--idle-timeout", type=int, default=0, help="Idle timeout in seconds")
@click.pass_context
def remote(
    ctx,
    function: list[str],
    allfunctions: bool,
    version: str,
    workerid: str,
    contextid: str,
    host: str,
    port: int,
    apikey: str = "",
    user: str = "",
    password: str = "",
    exchange: str = "processing-topic-exchange",
    vhost: str = "/",
    idle_timeout: int = 0,
    debug: bool = False,
    richformat: bool = False,
):
    """
    Connect to job-management remotely [Only available with the "remote" module]

    You can provide the --function/-f parameter multiple times or use --allfunctions/-af to
    expose multiple/all functions.
    The same function can be available in different versions. If a container is not responding
    to Job offers for a function there might be a mismatch between exposed and requested version
    of a function. You can use the '--allversions' parameter to respond to requests of any version,
    but this is recommended only for development uses.
    """
    # import here to avoid circular imports
    from pinexq.procon.runtime.worker import ProConWorker
    from pinexq.procon.runtime.foreman import ProConForeman

    # Get Step function from CLI-context
    step: Step = ctx.obj

    configure_logging(debug=debug, rich=richformat)
    log_version_info(log=True)

    # Validate and check input parameters
    if not exchange:
        raise ValueError("Exchange for RabbitMQ not set!")

    if not vhost:
        raise ValueError("Virtual host for RabbitMQ not set!")

    if function and allfunctions:
        raise ValueError("Provide either the --function or --allfunctions parameter, but not booth!")

    if version != "0":
        logger.warning("The 'VERSION' CLI parameter is deprecated!"
                       " Please use explicit versioning with the @version function decorator.")

    # Check that either an API-key xor the user/pw for RabbitMQ was given
    if not (apikey or (user and password)):
        raise ValueError("Provide either username and password or the API-key for RabbitMQ access!")
    elif apikey and (user or password):
        raise ValueError("Provide either username and password or the API-key for RabbitMQ access, but not both!")

    # If there is an API-key, split it into 3 parts
    #  we only use the "context-id" as username and the whole "apikey" as password
    if apikey:
        try:
            _, user, _ = apikey.split("_")
            password = apikey
        except ValueError as ex:
            raise ValueError("Unrecognized API-key format!  Expected:  '<namespace>_<context-id>_<key>'")

    remove_environment_variables(
        include=["PROCON_REMOTE_*", "KUBERNETES_*"]
    )

    try:
        worker = ProConWorker(
            step=step,
            function_names=["*"] if allfunctions else function,
            rmq_parameters={
                "host": host,
                "port": port,
                "login": user,
                "password": password,
                "exchange": exchange,
                "vhost": vhost,
            },
            worker_id=workerid,
            context_id=contextid,
            idle_timeout=idle_timeout,
        )
    except ProConUnknownFunctionError as ex:
        exit_unknown_function(step=step, func_name=ex.function_name)

    # noinspection PyUnboundLocalVariable
    ProConForeman(worker, debug=False)


@cli.command()
@click.option("-f", "--function", type=str, required=True, help="The function's name in this container.")
@click.option(
    "-n", "--name", type=str, help="Name under which the function is registered. Defaults to the function name."
)
@click.option("--api-url", type=str, required=True, help="URL to the JMA's API entry point.")
@click.option("--api-key", type=str, default=None, help="API-key to connect to the API.")
@click.option("--user-id", type=str, default=None, help="User-id to connect to the API, if not using an API-key")
@click.option("--user-group", type=str, default=None, help="User group under which to connect, implies user-id access.")
@click.option("-t", "--tag", type=str, multiple=True, default=[], help="Optional tags for the processing step.")
@click.option("-v", "--version", type=str, help="Custom value for the version.")
@click.pass_context
def register(
    ctx,
    function: str,
    name: str,
    api_url: str,
    api_key: str,
    user_id: str,
    user_group: str,
    tag: list[str],
    version: str,
):
    """Register a functions signature at the JobManagement via the API"""
    from httpx import Client
    from pinexq.client.job_management import ProcessingStep
    import pinexq_client

    if not is_valid_version_string(version):
        raise ValueError(f"Given version: '{version}' is not valid. Allowed: a-Z 0-9 and '_' '-' '.'")

    step: Step = ctx.obj

    # noinspection PyProtectedMember
    if function not in step._signatures:
        exit_unknown_function(step, function)

    # If no name to register is provided, default to the function name
    processing_step_name = name or function

    # Create the function manifest
    # noinspection PyProtectedMember
    schema = step._signatures[function]
    model = schema.get_function_model()
    manifest_dict = model.model_dump(by_alias=True)

    # rich.print_json(manifest_dict)

    # Connect to the JMA with a httpx client
    if user_id and api_key:
        raise click.BadParameter("The parameters --api-key and --user-id can not be provided at the same time.")

    if api_key:
        if user_group:
            raise click.BadParameter("Parameter --api-key does not allow --user-group")
        headers = {"x-api-key": api_key}
    elif user_id:
        if user_group:
            headers = {"x-user-id": user_id, "x-user-groups": user_group}
        else:
            headers = {"x-user-id": user_id}
    else:
        raise click.BadParameter("Either --api-key or --user-id must be provided.")

    client_instance = Client(
        base_url=api_url,
        headers=headers,
    )

    # Register the manifest using the API client
    try:
        processing_step = (
            ProcessingStep(client_instance)
            .create(  # 'title' and 'function_name' are the same (for now?)
                title=processing_step_name, function_name=processing_step_name, version=version
            )
            .upload_configuration(manifest_dict)
        )
        # If the user supplied tags, add them
        if tag:
            processing_step.set_tags(tag)

    # Print a compact error message instead of a stacktrace
    except pinexq.client.core.exceptions.ApiException as exc:
        details = exc.problem_details
        print(f"Error [{details.status}]: {details.title}\n-> {details.detail}")

    client_instance.close()


