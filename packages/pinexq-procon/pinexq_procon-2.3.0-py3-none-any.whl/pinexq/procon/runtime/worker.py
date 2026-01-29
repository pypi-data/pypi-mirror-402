import asyncio
import logging
from asyncio import CancelledError, Task
from typing import Awaitable, Callable, TypeVar, Union

import pydantic

from ..core.exceptions import (
    ProConBadMessage,
    ProConException,
    ProConMessageRejected,
    ProConShutdown,
    ProConUnknownFunctionError,
)
from ..core.naming import escape_version_string, is_valid_version_string
from ..remote.messages import (
    JobOfferMessageBody,
    WorkerCommandMessageBody,
    WorkerStatus,
)
from ..remote.rabbitmq import QueueSubscriber, RabbitMQClient
from ..step import Step
from .job import FunctionVersion, ProConJob
from .settings import JOB_OFFERS_TOPIC
from .tool import handle_task_result


log = logging.getLogger(__name__)

T = TypeVar('T')  # Any type.
CallableOrAwaitable = Union[Callable[[T], bool], Callable[[T], Awaitable[bool]]]


class WorkerCommunicationRMQ:
    """Worker-specific communication using RabbitMQ"""
    rmq_client: RabbitMQClient
    _job_offer_subs: list[QueueSubscriber]
    _outgoing_msg_queue: asyncio.Queue
    _worker_cmd_cb: CallableOrAwaitable[WorkerCommandMessageBody] | None

    def __init__(
            self,
            rmq_parameters: dict,
            sender_id: str,
            worker_id: str,
            context_id: str,
            functions: list[FunctionVersion],
            msg_queue: asyncio.Queue,
            worker_cmd_cb: CallableOrAwaitable[WorkerCommandMessageBody] | None = None,
    ):
        self.sender_id = sender_id
        self.worker_id = worker_id
        self.context_id = context_id
        self._functions = functions
        self._outgoing_msg_queue = msg_queue
        self._worker_cmd_cb = worker_cmd_cb
        self._job_offer_subs = []

        self.is_initialized = False

        self.rmq_parameters = rmq_parameters
        self.rmq_client = RabbitMQClient(**rmq_parameters)

    async def start(self):
        """Connect to the RabbitMQ server and start accepting jobs"""
        await self.rmq_client.connect_and_run()
        await self._connect_to_worker_queues(self._functions)

    async def stop(self):
        """Stop receiving jobs and disconnect from RMQ server"""
        await self.disconnect_from_worker_queues()
        await self.rmq_client.close()

    @property
    def is_ready_to_send(self) -> bool:
        """Returns if connection to RMQ server is established and queues initialized."""
        return self.rmq_client.is_connected and self.is_initialized

    async def report_worker_state(self, status: WorkerStatus | str):
        """Log the current state of the worker"""
        log.info(f"Worker state changed to: '{status.value}'")

    async def report_worker_error(self, title: str, exception: Exception | None = None):
        """Log error message from an exception"""
        if exception:
            log.exception(f"Error in worker: {title}", exc_info=exception)
        else:
            log.error(f"Error in worker: {title}")

    async def _create_job_offer_subscription(self, func_name: str, func_version: str) -> QueueSubscriber | None:
        topic = JOB_OFFERS_TOPIC.format(ContextId=self.context_id, FunctionName=func_name, Version=func_version)
        # log.debug("Subscribing to Job.Offers queue: '%s'", topic)
        exists = await self.rmq_client.does_queue_exist(topic)
        if exists:
            return await self.rmq_client.subscriber(
                queue_name=topic,
                routing_key=topic,
                callback=self.on_job_offer_message
            )
        else:
            return None

    async def _connect_to_worker_queues(self, functions: list[FunctionVersion]):
        """
        Create the worker command channel, subscribe to the status channel,
        and subscribe to a `job.offer` channel for each function this worker publishes.

        Args:
            functions: List of tuples with ("the_function_name", "version")
        """

        self._job_offer_subs = []
        for f in functions:
            sub = await self._create_job_offer_subscription(func_name=f.name, func_version=f.version)
            if sub:
                self._job_offer_subs.append(sub)
                log.info(f"Listening for JobOffers: {f.name}:{f.version}")
            else:
                log.warning(f"Could not connect to JobOffers of: {f.name}:{f.version}")

        if not self._job_offer_subs:
            log.critical(msg:="Failed to connect to any Job.Offer queues!")
            raise ProConException(msg)

        self.is_initialized = True

    async def disconnect_from_worker_queues(self):
        """Stop listening to job.offer queues and stop & delete the command queue for this worker."""
        if not self.is_initialized:
            return
        await asyncio.gather(
            *(sub.stop_consumer_loop() for sub in self._job_offer_subs)
        )

        self.is_initialized = False

    async def start_consuming_job_offers(self):
        """Start polling on all `job.offer` queues."""
        try:
            async with asyncio.TaskGroup() as group:
                for i, sub in enumerate(self._job_offer_subs):
                    group.create_task(sub.run_consumer_loop(), name=f"job-offer-consumer-{i}")

        except ExceptionGroup as eg:
            for exc in eg.exceptions:
                log.error(f"Error in Job.Offer consumer loop! {exc}")
                # log.exception("Error in Job.Offer consumer loop!", exc_info=exc)
            raise

    async def stop_consuming_job_offers(self):
        """Stop polling on all `job.offer` queues."""
        await asyncio.gather(
            *(sub.stop_consumer_loop() for sub in self._job_offer_subs)
        )

    #  Protocol handlers ------------------------

    async def on_job_offer_message(self, message: str | bytes):
        """Process the raw message body of incoming job.offers"""
        try:
            job_offer_msg = JobOfferMessageBody.model_validate_json(message)
        except pydantic.ValidationError as ex:
            msg = "Deserialization of 'job.offer' message failed!"
            await self.report_worker_error(msg, exception=ex)
            log.exception("⚠ %s", msg, exc_info=ex)
            raise ProConBadMessage(msg) from ex
        else:
            log.debug("'job.offer' message deserialized: %s", str(job_offer_msg))
            try:
                self._outgoing_msg_queue.put_nowait(job_offer_msg)
            except asyncio.QueueFull:
                # A full message queue indicates that the worker is busy. The worker
                # should have stopped receiving further job.offer messages. If we
                # receive a message nonetheless (e.g. due to concurrency or prefetch)
                # reject the message back to the queue.
                raise ProConMessageRejected("Worker busy -> Job.offer rejected!")

    async def on_worker_cmd_message(self, message: str | bytes):
        """Process the raw message body of incoming worker.commands"""
        try:
            job_cmd_msg = WorkerCommandMessageBody.model_validate_json(message)
        except pydantic.ValidationError as ex:
            job_cmd_msg = "Deserialization of 'worker.command' message failed!"
            await self.report_worker_error(job_cmd_msg, exception=ex)
            log.exception("⚠ %s", job_cmd_msg, exc_info=ex)
        else:
            log.debug("'worker.command' message deserialized: %s", str(job_cmd_msg))
            raise NotImplementedError('Worker commands not yet supported!')
            # if self._worker_cmd_cb is not None:
            #     result = self._worker_cmd_cb(job_cmd_msg)
            #     if isawaitable(result):
            #         await result


class ProConWorker:
    """
    Worker class providing a `Step` function as remote resource via RabbitMQ
    and handling its execution.

    This class is instantiated and supervised by the Foreman class.
    """

    _job_task: Task | None = None
    _processing_task: Task | None = None
    _worker_com: WorkerCommunicationRMQ
    _busy_lock: asyncio.BoundedSemaphore
    _message_queue: asyncio.Queue
    _running: asyncio.Event

    step: Step
    connected: bool
    available_functions: dict[str, str]
    configured_functions: dict[str, str]

    def __init__(
        self,
        step: Step,
        function_names: list[str],
        rmq_parameters: dict,
        worker_id: str,
        context_id: str,
        idle_timeout: int = 0,
    ):
        """Initialize a worker that can offer multiple Step functions for remote execution.
        Functions are executed one at a time according to job.offer messages received via
        RabbitMQ (RMQ) queues.

        Args:
            step: Step class containing the functions.
            function_names: A list of function names to be offered remotely.
            rmq_parameters: RabbitMQ connection parameters.
            worker_id: Unique identifier for this worker.
            context_id: Context id this worker is running in.
            idle_timeout: Maximum idle time in seconds
        """
        log.info("Initializing worker for function '%s'", function_names)
        self.worker_id = worker_id
        self.context_id = context_id
        self.step = step
        self.connected = False

        # Functions as defined in the `Step` class (name and version)
        self.available_functions = {
            name: escape_version_string(signature.version)
            for name, signature in self.step.step_signatures.items()
        }

        # Functions configured by the --function/-f commandline parameter
        self.configured_functions = self.resolve_function_and_version(function_names)

        # This event is set when the worker is actively receiving job.offers
        self._running = asyncio.Event()

        # Semaphore limiting the number of concurrently started Jobs.
        # Currently, there is only one worker that can process a single job.
        self._busy_lock = asyncio.BoundedSemaphore(value=1)

        # Incoming job.offer messages are passed through this message queue.
        # This limits the number of messages pre-fetched from the RMQ queue.
        self._incoming_msg_queue = asyncio.Queue(maxsize=1)

        self._worker_com = WorkerCommunicationRMQ(
            rmq_parameters=rmq_parameters,  # TODO: make this a dataclass
            sender_id=self.sender_id,
            worker_id=self.worker_id,
            context_id=self.context_id,
            functions=[
                FunctionVersion(name=name, version=version)
                for name, version in self.configured_functions.items()
            ],
            msg_queue=self._incoming_msg_queue
        )

        self.idle_timeout = idle_timeout

    async def run(self) -> None:
        """Connect to the RabbitMQ server and start accepting jobs"""
        try:
            async with asyncio.TaskGroup() as group:
                log.info("Starting worker communication ...")
                await self._worker_com.start()
                await self._worker_com.report_worker_state(WorkerStatus.starting)
                group.create_task(self._worker_com.start_consuming_job_offers())

                log.info("▶ Start processing jobs")
                await self._worker_com.report_worker_state(WorkerStatus.running)

                group.create_task(self.process_jobs(), name="process_jobs")

        except* ProConShutdown as exc:
            log.info(f"Worker is shutting down! Reason: {str(exc)}")

        except* CancelledError:
            log.warning("Worker got cancelled!")

        except* ProConException as exc:
            log.exception(f"Unhandled exception in worker! -> {str(exc)}")

        finally:
            log.info("⏹ Stopped processing jobs")
            await self._worker_com.report_worker_state(WorkerStatus.exiting)
            await self._worker_com.stop()

    @property
    def sender_id(self) -> str:
        """Unique sender ID of this worker"""
        return f"worker:{self.worker_id}"

    def resolve_function_and_version(self, function_version_strings: list[str]) -> dict[str, str]:
        """Resolves a list with "function_name:version" specifiers.
        Check if container exposes the given function names,
        substitute '*' with all available names and split off the version string.
        """
        # If the requested functions contain a wildcard, just return all available functions
        if "*" in function_version_strings:
            return self.available_functions

        function_version_dict: dict[str, str] = {}
        for s in function_version_strings:
            # Split function+version string at the first colon
            name, _, version = s.partition(":")

            if name not in self.available_functions:
                raise ProConUnknownFunctionError(f"Unknown function: '{name}'!", func_name=name)

            # If no version was provided as parameter, return the version annotated at the function
            if not version:
                version = self.available_functions[name]
            else:
                if not is_valid_version_string(version):
                    raise ValueError(f"Given version: '{version}' is not valid. Allowed: a-Z 0-9 and '_' '-' '.'")

            # Ensure the version string contains no '.' so we don't mess with messaging
            version = escape_version_string(version)

            function_version_dict[name] = version

        return function_version_dict

    def check_function_from_offer(self, job_offer_msg: JobOfferMessageBody) -> FunctionVersion | None:
        """Ensures that the function and version in the job.offer is available in this container."""

        if (function_name := job_offer_msg.content.algorithm) not in self.configured_functions:
            msg = (f"Received job offer for unknown function: '{function_name}'!"
                   f" Available are: {list(self.configured_functions.keys())}")
            log.error(msg)
            raise ProConUnknownFunctionError(msg)

        requested_version = escape_version_string(job_offer_msg.content.algorithm_version)
        available_version = self.configured_functions[function_name]
        if requested_version != available_version:
            msg = (
                f"Function '{function_name}' is available in version '{available_version}', "
                f"but the requested version is: '{requested_version}'"
            )
            log.error(msg)
            raise ProConUnknownFunctionError(msg)

        return FunctionVersion(name=function_name, version=requested_version)

    async def run_job(self, job_offer_msg: JobOfferMessageBody) -> None:
        """Run a specific job according to a job.offer message."""

        function_and_version = self.check_function_from_offer(job_offer_msg)

        await self._busy_lock.acquire()
        try:
            job = ProConJob(
                step=self.step,
                function=function_and_version,
                context_id=self.context_id,
                job_offer=job_offer_msg.content,
                _rmq_client=self._worker_com.rmq_client,
            )
            await job.start()
            await job.process()
        except Exception:
            raise
        finally:
            self._busy_lock.release()

    async def process_jobs(self):
        """Processing loop for incoming `job.offer` messages."""
        log.debug("🔄 Entering processing loop.")
        self._running.set()
        while self._running.is_set():
            try:
                if self.idle_timeout > 0:
                    log.info(f"Idle timeout set to: {self.idle_timeout}s")
                    async with asyncio.timeout(delay=self.idle_timeout):
                        message = await self._incoming_msg_queue.get()
                else:
                    message = await self._incoming_msg_queue.get()

            except (TimeoutError, asyncio.TimeoutError):
                log.info(f"⌛ Idle timeout! Worker was idle for more than {self.idle_timeout}s.")
                raise ProConShutdown("Idle-timeout exceeded")
            except asyncio.CancelledError:
                raise ProConShutdown("Processing loop canceled")

            try:
                self._job_task = asyncio.create_task(self.run_job(message), name="job_main")
                await self._job_task
            except CancelledError:
                pass  # Wait for the computation to finish, when this task is cancelled
            finally:
                self._incoming_msg_queue.task_done()

        self._running.clear()
        log.debug("⏹ Exiting processing loop.")
        raise ProConShutdown("Processing loop stopped")

    async def stop(self, timeout: float | None = None) -> None:
        """Stop the processing loop for incoming job offers.
        If a job is still running, wait for the computation to finish."""
        self._running.clear()
        await self._worker_com.stop_consuming_job_offers()

        # Wait for running jobs by waiting for the busy lock
        if self._busy_lock.locked():
            log.debug("Waiting for running Job to finish ...")
            await asyncio.wait_for(self._busy_lock.acquire(), timeout=timeout)
            self._busy_lock.release()

        # Force the processing loop to exit, when waiting for the queue's .get()
        if self._processing_task is not None:
            self._processing_task.cancel()

    def _on_idle_timeout(self) -> None:
        """A wrapper to call self.stop() from synchronous code."""
        log.info("Worker reached idle timeout. Shutting down ...")
        self._stop_task = asyncio.create_task(self.stop(), name="stop-worker-task")
        self._stop_task.add_done_callback(handle_task_result)

    async def _on_worker_cmd(self, worker_cmd_msg: WorkerCommandMessageBody) -> None:
        # TODO
        raise NotImplementedError()
