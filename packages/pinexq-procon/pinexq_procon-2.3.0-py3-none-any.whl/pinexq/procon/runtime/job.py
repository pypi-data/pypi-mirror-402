import asyncio
import functools
import logging
import uuid
from asyncio import Task
from dataclasses import dataclass, field
from functools import cached_property
from inspect import isawaitable
from typing import Any, Awaitable, Callable, TypeVar, Union

import pydantic

from ..core.exceptions import ProConException
from ..dataslots import DataSlotDescription, Metadata, SlotDescription
from ..dataslots.metadata import CallbackMetadataHandler
from ..remote.messages import (
    DataslotInput,
    DataslotOutput,
    ErrorContent,
    JobCommandMessageBody,
    JobOfferContent,
    JobResultContent,
    JobResultMessageBody,
    JobResultMetadataContent,
    JobResultMetadataMessageBody,
    JobStatus,
    JobStatusContent,
    JobStatusMessageBody,
    MessageHeader,
    MetadataUpdate,
    SlotInfo,
)
from ..remote.rabbitmq import QueuePublisher, QueueSubscriber, RabbitMQClient
from ..runtime.settings import (
    JOB_COMMAND_TOPIC,
    JOB_RESULT_TOPIC,
    JOB_STATUS_TOPIC,
)
from ..runtime.tool import handle_task_result
from ..step import Step
from ..step.step import ExecutionContext


log = logging.getLogger(__name__)

T = TypeVar('T')  # Any type.
CallableOrAwaitable = Union[Callable[[T], None], Callable[[T], Awaitable[None]]]


@dataclass
class FunctionVersion:
    name: str
    version: str


def _create_dataslot_description(
    dataslots: list[DataslotInput] | list[DataslotOutput]
) -> dict[str, DataSlotDescription]:
    """Convert the dataslot format from messages to the internal format"""
    dataslot_description = {}
    for ds in dataslots:
        # Input and output dataslots have different attribute names for their list of slots
        msg_slots = ds.sources if isinstance(ds, DataslotInput) else ds.destinations
        slots = [
            SlotDescription(
                uri=str(slot.uri),
                headers=(
                    {h.Key: h.Value for h in slot.prebuildheaders}
                    if slot.prebuildheaders is not None
                    else {}
                ),
                mediatype=slot.mediatype,
            )
            for slot in msg_slots
        ]
        dataslot_description[ds.name] = DataSlotDescription(
            name=ds.name, slots=slots
        )

    return dataslot_description


@dataclass
class RemoteExecutionContext(ExecutionContext):
    """Wraps all information to call a function in a Step container.

    Extends the basic contex with information from the JobManagement.
    """

    current_job_offer: JobOfferContent | None = field(default=None)

@dataclass
class JobInfo:
    """Wraps all information to start a single job."""
    context_id: str
    function_name: str
    version: str
    job_id: str | None = None


def format_topic(format_str: str, job_info: JobInfo) -> str:
    """Creates the RabbitMQ topic/queue names from a format string definition."""
    return format_str.format(
        JobId=job_info.job_id,
        ContextId=job_info.context_id,
        FunctionName=job_info.function_name,
        Version=job_info.version
    )


class JobCommunicationRMQ:
    """Job-specific communication using RabbitMQ"""

    _job_command_sub: QueueSubscriber
    _job_status_pub: QueuePublisher
    _job_result_pub: QueuePublisher
    _job_progress_pub: QueuePublisher
    _rmq_client: RabbitMQClient
    _job_cmd_cb: CallableOrAwaitable[JobCommandMessageBody] | None
    _consumer_task: asyncio.Task | None

    job_id: uuid.uuid4

    def __init__(
            self,
            rmq_client: RabbitMQClient,
            job_info: JobInfo,
            job_cmd_cb: CallableOrAwaitable[JobCommandMessageBody] | None = None
    ):
        self._rmq_client = rmq_client
        self.job_info = job_info
        self._job_cmd_cb = job_cmd_cb
        self.is_initialized = False

    @property
    def sender_id(self) -> str:
        return f"job:{self.job_info.job_id}"

    async def start(self):
        await self.connect_to_job_queues()
        self.is_initialized = True

    async def stop(self):
        await self._job_command_sub.stop_consumer_loop()
        self.is_initialized = False

    @property
    def is_ready_to_send(self) -> bool:
        return self._rmq_client.is_connected and self.is_initialized

    async def connect_to_job_queues(self):
        cmd_topic = format_topic(JOB_COMMAND_TOPIC, self.job_info)
        log.debug("Subscribing to Job.Command queue: '%s'", cmd_topic)

        # Connect to the _Job.Command_ queue
        if await self._rmq_client.does_queue_exist(cmd_topic):
            self._job_command_sub = await self._rmq_client.subscriber(
                queue_name=cmd_topic,
                routing_key=cmd_topic,
                callback=self.on_job_cmd_message
            )
            self._consumer_task = asyncio.create_task(
                self._job_command_sub.run_consumer_loop(), name="job-cmd-consumer"
            )
            self._consumer_task.add_done_callback(
                functools.partial(handle_task_result, description="Job.Command consumer task")
            )
        else:
            log.error(f"Job.Command queue: {cmd_topic} does not exist, Job will be processed but no commands accepted.")

        # Prepare the _Job.Status_ topic
        status_topic = format_topic(JOB_STATUS_TOPIC, self.job_info)
        log.debug("Connecting to Job.Status queue: '%s'", status_topic)
        self._job_status_pub = await self._rmq_client.publisher(
            routing_key=status_topic,
        )

        # Prepare the _Job.Result_ topic
        result_topic = format_topic(JOB_RESULT_TOPIC, self.job_info)
        log.debug("Connecting to Job.Result queue: '%s'", result_topic)
        self._job_result_pub = await self._rmq_client.publisher(
            routing_key=result_topic,
        )

    async def on_job_cmd_message(self, message: str | bytes):
        try:
            msg = JobCommandMessageBody.model_validate_json(message)
        except pydantic.ValidationError as ex:
            msg = "Deserialization of 'job.command' message failed!"
            await self.report_job_error(msg, cause=ex)
            log.exception("⚠ %s", msg, exc_info=ex)
        else:
            log.debug("'job.command' message deserialized: %s", str(msg))
            if self._job_cmd_cb is not None:
                result = self._job_cmd_cb(msg)
                if isawaitable(result):
                    await result
            else:
                log.warning("Job command message received, but no handler is set!")

    async def send_job_status(self, msg: JobStatusMessageBody):
        json_msg = msg.model_dump_json(by_alias=True)
        await self._job_status_pub.send(json_msg)

    async def send_job_result(self, msg: JobResultMessageBody | JobResultMetadataMessageBody):
        if not self.is_ready_to_send:
            log.warning('Job communication not initialized. Skip sending "%s" message.', str(msg.type_))
            return
        json_msg = msg.model_dump_json(by_alias=True)
        await self._job_result_pub.send(json_msg)

    async def report_job_status(self, status: JobStatus):
        """Publishes the current state of the STM to 'Worker.Status.*'"""
        content = JobStatusContent(job_id=self.job_info.job_id, status=status)
        msg = JobStatusMessageBody(
            header=MessageHeader(sender_id=self.sender_id, ),
            content=content,
        )
        await self.send_job_status(msg)

    async def report_job_error(self, title: str, cause: Exception | str):
        """Publishes an error message from an exception to 'Worker.Status.*'"""
        if isinstance(cause, ProConException) and cause.user_message:
            content = ErrorContent(
                title=title, detail=cause.user_message, instance=f"job:{self.job_info.job_id}"
            )
        elif isinstance(cause, Exception):
            content = ErrorContent.from_exception(
                title=title, exception=cause, instance=f"job:{self.job_info.job_id}"
            )
        else:
            content = ErrorContent(
                title=title, detail=cause, instance=f"job:{self.job_info.job_id}"
            )

        msg = JobStatusMessageBody(
            header=MessageHeader(sender_id=self.sender_id, ),
            content=content,
        )
        await self.send_job_status(msg)

    async def report_job_result(self, result: Any):
        msg = JobResultMessageBody(
            header=MessageHeader(sender_id=self.sender_id, ),
            content=JobResultContent(job_id=self.job_info.job_id, result=result),
        )
        await self.send_job_result(msg)

    async def report_job_result_metadata(self, metadata_content: JobResultMetadataContent):
        msg = JobResultMetadataMessageBody(
            header=MessageHeader(sender_id=self.sender_id, ),
            content=metadata_content,
        )
        await self.send_job_result(msg)


class ProConJob:
    """Business logic to run a single Job"""

    _job_com: JobCommunicationRMQ
    _background_tasks: set[Task]

    step: Step
    job_offer: JobOfferContent
    job_info: JobInfo
    status: JobStatus

    def __init__(
            self,
            step: Step,
            function: FunctionVersion,
            context_id: str,
            job_offer: JobOfferContent,
            _rmq_client: RabbitMQClient,
    ):
        self.step = step
        self.job_offer = job_offer
        self.job_info = JobInfo(
            job_id=str(job_offer.job_id),
            context_id=context_id,
            function_name=function.name,
            version=function.version,
        )
        self.status = JobStatus.starting

        self._background_tasks = set()

        self._event_loop = asyncio.get_event_loop()

        self._job_com = JobCommunicationRMQ(
            rmq_client=_rmq_client,
            job_info=self.job_info,
            job_cmd_cb=self._on_job_cmd
        )

    async def start(self):
        await self._job_com.start()
        await self._job_com.report_job_status(self.status)

    async def disconnect_from_job_queues(self):
        await self._job_com.stop()

    async def process(self):
        log.info("Start processing Job <id: %s>", self.job_info.job_id)
        self.status = JobStatus.running
        await self._job_com.report_job_status(self.status)

        if self.job_info.function_name != self.job_offer.algorithm:
            msg = (
                f"The algorithm in the job offer '{self.job_offer.algorithm}' does "
                f"not match the function name of this container ('{self.job_info.function_name}')!"
            )
            log.error(msg)
            await self._job_com.report_job_error(title="Algorithm mismatch!", cause=msg)
        else:
            await self.call_step_function()

        self.status = JobStatus.finished
        await self._job_com.report_job_status(self.status)
        await self.disconnect_from_job_queues()

        log.info("Stop processing Job <id: %s>", self.job_info.job_id)

    async def call_step_function(self):
        """Entrypoint for a step function's execution when running as a worker"""
        context = RemoteExecutionContext(
            function_name=self.job_info.function_name,
            parameters=self.job_offer.parameters or {},
            input_dataslots=_create_dataslot_description(self.job_offer.input_dataslots),
            output_dataslots=_create_dataslot_description(self.job_offer.output_dataslots),
            current_job_offer=self.job_offer,
            metadata_handler=self._get_slot_metadata_handler(),
        )
        try:
            # noinspection PyProtectedMember
            result = await asyncio.to_thread(
                self.step._call,
                context=context
            )
        except Exception as ex:
            msg = f"Exception while processing job <id:{self.job_info.job_id}>"
            log.exception(msg, exc_info=ex)
            await self._job_com.report_job_error(title=msg, cause=ex)
        else:
            log.info("Job finished successfully.")
            await self._job_com.report_job_result(result)

    def _get_slot_metadata_handler(self):
        # Create the handler that will be called when accessing a Slot's metadata
        return CallbackMetadataHandler(
            getter=self._get_slot_metadata,
            setter=self._set_slot_metadata
        )

    @cached_property
    def _all_dataslots(self) -> dict[str, list[SlotInfo]]:
        # Reduce in-/output dataslots into one dict, that is created and cached on first access
        input_dataslots = {s.name: s.sources for s in self.job_offer.input_dataslots}
        output_dataslots = {s.name: s.destinations for s in self.job_offer.output_dataslots}
        return input_dataslots | output_dataslots

    def _get_slot_metadata(self, slot: SlotDescription) -> Metadata:
        # Get the metadata from the in-/output slot description in the job.offer
        dataslots = self._all_dataslots
        return dataslots[slot.dataslot_name][slot.index].metadata

    def _set_slot_metadata(self, slot: SlotDescription, metadata: Metadata) -> None:
        # Send a job.result.metadata message
        meta_content = JobResultMetadataContent(
            updates=[
                MetadataUpdate(dataslot_name=slot.dataslot_name, slot_index=slot.index, metadata=metadata)
            ]
        )
        # Fire and forget the task, but keep a reference to prevent being garbage collected
        task = self._event_loop.create_task(
            self._job_com.report_job_result_metadata(meta_content), name="set_metadata"
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        task.add_done_callback(handle_task_result)

    async def _on_job_cmd(self, message: JobCommandMessageBody):
        log.debug("Job command received: %s", message)
        raise NotImplementedError()
