from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto

from pydantic import BaseModel, Field


class MediaTypes(StrEnum):
    OCTETSTREAM = 'application/octet-stream'
    JSON = 'application/json'
    FORMDATA = 'multipart/form-data'
    SIREN = 'application/siren+json'
    XML = 'application/xml'
    ZIP = 'application/zip'
    PDF = 'application/pdf'
    TEXT = 'text/plain'
    HTML = 'text/html'
    CSV = 'text/csv'
    SVG = 'image/svg+xml'
    PNG = 'image/png'
    JPEG = 'image/jpeg'
    BMP = 'image/bmp'
    WORKFLOW_DEFINITION = "application/vnd.pinexq.workflow.definition+json"
    WORKFLOW_REPORT = "application/vnd.pinexq.workflow.report+json"


class SlotType(Enum):
    INPUT = auto()
    OUTPUT = auto()
    RETURN = auto()


@dataclass(eq=True, slots=True)
class SlotDescription:
    uri: str
    index: int = field(default=0)
    dataslot_name: str = field(default_factory=str)
    headers: dict[str, str] = field(default_factory=dict)
    mediatype: str = field(default_factory=str)


@dataclass(eq=True, slots=True)
class DataSlotDescription:
    name: str
    slots: list[SlotDescription]


class Metadata(BaseModel):
    comment: str = Field(default="")
    tags: list[str] = Field(default_factory=list)
    filename: str = Field(default="")
