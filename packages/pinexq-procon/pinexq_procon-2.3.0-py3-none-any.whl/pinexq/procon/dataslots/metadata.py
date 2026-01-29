import json
import logging
from pathlib import Path
from typing import Callable, Protocol, Sequence, TypeVar

from ..dataslots.datatypes import Metadata, SlotDescription


LOG = logging.getLogger(__name__)


def metadata_to_json(meta: Metadata) -> str:
    return meta.model_dump_json()


def json_to_metadata(data: str) -> Metadata:
    return Metadata(**json.loads(data))


class MetadataProxy:
    """
    Getter/setter methods for controlled user access to a Metadata object.

    If no Metadata object is provided for initialization, this class will assign a default
    on first access of any metadata property.
    """
    __slots__ = ('_metadata', '_readonly')

    _metadata: Metadata
    _readonly: bool

    def __init__(self, metadata: Metadata, _readonly: bool = False):
        self._metadata = metadata
        self._readonly = _readonly

    def __bool__(self):
        """Return True if Metadata was set."""
        return len(self._metadata.comment) > 0 or len(self._metadata.tags) > 0

    @property
    def comment(self) -> str:
        """Comments assigned to the Workdata of this slot."""
        return self._metadata.comment

    @comment.setter
    def comment(self, s: str):
        if self._readonly:
            raise AttributeError("Metadata on this slot is read-only! Can not set 'comment'.")
        self._metadata.comment = s

    @property
    def tags(self) -> tuple[str, ...] | list[str]:
        """Tags assigned to the Workdata of this slot.

        Returns a list of tags if the metadata is writable (e.g. OUTPUT-slot)
        or an immutable tuple if metadata is read-only (e.g. INPUT slots)
        """
        if self._readonly:
            return tuple(self._metadata.tags)
        return self._metadata.tags

    @tags.setter
    def tags(self, tag_list: Sequence[str]):
        if self._readonly:
            raise AttributeError("Metadata on this slot is read-only! Can not set 'tags'.")
        self._metadata.tags = list(tag_list)

    @property
    def filename(self) -> str:
        """Original filename that was uploaded as Workdata. This is independent of the
        filename accessed by the backend of the Slot, which can vary depending on the implementation."""
        return self._metadata.filename

    @filename.setter
    def filename(self, s: str):
        if self._readonly:
            raise AttributeError("Metadata on this slot is read-only! Can not set 'filename'.")
        self._metadata.filename = s

    def __repr__(self):
        return self._metadata.__repr__()

    def is_readonly(self) -> bool:
        """True if the metadata is readonly."""
        return self._readonly


class MetadataHandler(Protocol):
    """Defines the expected interface how to read/write metadata."""

    def get(self, slot: SlotDescription) -> Metadata:
        ...

    def set(self, slot: SlotDescription, metadata: Metadata):
        ...


class LocalFileMetadataStore(MetadataHandler):
    """Store metadata as a '.meta' sidecar file next to file defined in the slot's description uri."""

    @staticmethod
    def _metadata_path_from_description(slot: SlotDescription) -> Path:
        slot_path = Path(slot.uri)
        return slot_path.with_name(f"{slot_path.name}.meta")

    def get(self, slot: SlotDescription) -> Metadata | None:
        meta_path = self._metadata_path_from_description(slot)
        if meta_path.exists():
            return Metadata.model_validate_json(meta_path.read_text())
        else:
            return None

    def set(self, slot: SlotDescription, metadata: Metadata):
        meta_path = self._metadata_path_from_description(slot)
        meta_json = metadata.model_dump_json()
        meta_path.write_text(meta_json)


TSetCb = TypeVar('TSetCb', bound=Callable[[SlotDescription, Metadata], None])
TGetCb = TypeVar('TGetCb', bound=Callable[[SlotDescription,], Metadata])


class CallbackMetadataHandler(MetadataHandler):
    """Generic call/callback-interface to get and set metadata"""

    _setter_callback: TSetCb
    _getter_callback: TGetCb

    def __init__(self, setter: TSetCb, getter: TGetCb):
        self._setter_callback = setter
        self._getter_callback = getter

    def get(self, slot: SlotDescription) -> Metadata:
        return self._getter_callback(slot)

    def set(self, slot: SlotDescription, metadata: Metadata):
        self._setter_callback(slot, metadata)
