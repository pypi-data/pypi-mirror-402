"""
Message type definitions for the RabbitMQ communication.

https://dev.azure.com/data-cybernetics/Rymax-One/_wiki/wikis/General/105/Processing-communication-design
"""
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import AnyUrl, BaseModel, Field, constr

from ..dataslots import Metadata


class MessageModel(BaseModel):
    pass


class HeartbeatContent(MessageModel):
    type_: Literal['heartbeat'] = Field('heartbeat', alias='$type')


# class JobQuota(MessageModel):
#     type_: Literal['quota'] = Field('quota', const=True, alias='$type')
#     runtime: Optional[timedelta]
#     cpu_time: Optional[float]
#     qpu_time: Optional[float]
#     max_storage: Optional[int]

class Header(BaseModel):
    Key: str
    Value: str


class SlotInfo(BaseModel):
    uri: AnyUrl
    prebuildheaders: list[Header] | None
    mediatype: str
    metadata: Metadata | None = None


class DataslotInput(BaseModel):
    name: str
    sources: list[SlotInfo]
    # metadata: str


class DataslotOutput(BaseModel):
    name: str
    destinations: list[SlotInfo]
    # metadata: str


class JobExecutionContext(BaseModel):
    job_url: str
    access_token: str | None


class JobOfferContent(MessageModel):
    type_: Literal['job.offer'] = Field('job.offer', alias='$type')
    job_id: UUID
    algorithm: str
    algorithm_version: Optional[str] = None
    parameters: Optional[Any] = None
    # quota: Optional[JobQuota]
    priority: Optional[int] = None
    input_dataslots: list[DataslotInput]
    output_dataslots: list[DataslotOutput]
    job_execution_context: JobExecutionContext


class JobStatus(Enum):
    starting = 'starting'
    running = 'running'
    finished = 'finished'


class JobStatusContent(MessageModel):
    type_: Literal['job.status'] = Field('job.status', alias='$type')
    job_id: UUID
    status: JobStatus
    content: Optional[Any] = None


class JobProgressContent(MessageModel):
    type_: Literal['job.progress'] = Field('job.progress', alias='$type')
    job_id: UUID
    status: JobStatus
    content: Optional[Any] = None


class JobCommand(Enum):
    status = 'status'
    abort = 'abort'


class JobCommandContent(MessageModel):
    type_: Literal['job.command'] = Field('job.command', alias='$type')
    job_id: UUID
    command: JobCommand


class JobResultContent(MessageModel):
    type_: Literal['job.result'] = Field('job.result', alias='$type')
    job_id: UUID
    result: Any
    # quota: Optional[JobQuota]


class MetadataUpdate(BaseModel):
    dataslot_name: str
    slot_index: Annotated[int, Field(ge=0)]
    metadata: Metadata


class JobResultMetadataContent(MessageModel):
    type_: Literal['job.dataslot.metadata'] = Field('job.dataslot.metadata', alias='$type')
    updates: list[MetadataUpdate]


class WorkerStatus(Enum):
    starting = 'starting'
    idle = 'idle'
    running = 'running'
    stopped = 'stopped'
    exiting = 'exiting'


class WorkerStatusContent(MessageModel):
    type_: Literal['worker.status'] = Field('worker.status', alias='$type')
    worker_id: str
    status: WorkerStatus
    content: Optional[Any] = None


class WorkerCommand(Enum):
    start = 'start'
    stop = 'stop'
    status = 'status'
    abort = 'abort'
    restart = 'restart'
    shutdown = 'shutdown'


class WorkerCommandContent(MessageModel):
    type_: Literal['worker.command'] = Field('worker.command', alias='$type')
    worker_id: str
    command: WorkerCommand


class ErrorContent(MessageModel):
    type_: Literal['error'] = Field('error', alias='$type')
    type: str = Field('/procon/error')
    title: str
    detail: str
    instance: str
    metadata: Optional[dict] = None

    @classmethod
    def from_exception(cls, *args, exception: Exception, **kwargs) -> 'ErrorContent':
        """Generates the error message from an exception"""
        return cls(
            *args,
            detail=f'{type(exception).__name__}: {exception}',
            **kwargs
        )


# ID string of a service (worker, job, api) in the header;
#  format: <service>:<instance id>:<sub id>
# SenderID = pydantic.constr(regex=r'^[\w-]+:[\w-]+(:[\w-]+)?$')
SenderID = str  # don't validate the id format for now


class MessageHeader(MessageModel):
    type_: Literal['header'] = Field('header', alias='$type')
    sender_id: SenderID
    msg_id: UUID = Field(default_factory=uuid4)
    date: datetime = Field(default_factory=datetime.utcnow)
    version: Literal['1.0'] = '1.0'


class MessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[
        JobOfferContent, JobStatusContent, JobProgressContent,
        JobCommandContent, JobResultContent,
        JobResultMetadataContent,
        WorkerStatusContent, WorkerCommandContent,
        HeartbeatContent, ErrorContent
    ] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class JobOfferMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[JobOfferContent, ErrorContent] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class WorkerCommandMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[WorkerCommandContent, ErrorContent] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class WorkerStatusMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[WorkerStatusContent, ErrorContent] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class JobCommandMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[JobCommandContent, ErrorContent] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class JobStatusMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: Union[JobStatusContent, ErrorContent] = Field(..., discriminator='type_')
    metadata: Optional[Any] = None


class JobResultMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: JobResultContent
    metadata: Optional[Any] = None


class JobResultMetadataMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: JobResultMetadataContent
    metadata: Optional[Any] = None


class JobProgressMessageBody(MessageModel):
    type_: Literal['message'] = Field('message', alias='$type')
    header: MessageHeader
    content: JobProgressContent
    metadata: Optional[Any] = None
