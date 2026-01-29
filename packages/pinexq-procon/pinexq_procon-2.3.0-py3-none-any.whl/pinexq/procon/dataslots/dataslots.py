import logging
import pathlib
import warnings
from functools import partial
from typing import IO, Any, Self, Type, TypeVar, Union

from ..core.exceptions import ProConDataslotError
from ..dataslots.annotation import RETURN_SLOT_NAME, FileMode, ReaderType, WriterType, dataslot
from ..dataslots.datatypes import DataSlotDescription, MediaTypes, Metadata, SlotDescription, SlotType
from ..dataslots.filebackend import FileBackEnd, LocalCachedHttpFile, LocalFile
from ..dataslots.metadata import MetadataHandler, MetadataProxy


PathLike = TypeVar("PathLike", str, pathlib.Path)

LOG = logging.getLogger(__name__)


def create_dataslot_description(slots: dict[str, list[str]]) -> dict[str, DataSlotDescription]:
    """Create a dataslot description to pass on to the _call function of the Step class.

    The description is usually created internally
    from the information in a `job.offer` message or cli call.
    """
    return {
        name: DataSlotDescription(
            name=name, slots=[SlotDescription(p, i) for i, p in enumerate(path_list)]
        )
        for name, path_list in slots.items()
    }


def ishttp(uri: str) -> bool:
    return uri.startswith(('http://', 'https://'))


def _select_backend(description: SlotDescription) -> Type[FileBackEnd]:
    """Factory for selecting the backend for a Slot depending on the URI"""
    # Todo: use a match .. case here for pattern matching
    if ishttp(str(description.uri)):
        return partial(LocalCachedHttpFile, request_args={'headers': description.headers})
    else:
        # Todo: do all file paths reach here?  relative paths might be problematic?
        # https://stackoverflow.com/questions/11687478/convert-a-filename-to-a-file-url
        # https://stackoverflow.com/questions/5977576/is-there-a-convenient-way-to-map-a-file-uri-to-os-path
        return LocalFile


class Slot:
    """Wraps functionality for a single slot (i.e. one uri/file containing data)"""

    _name: str
    _type: SlotType
    _description: SlotDescription
    _backend: FileBackEnd
    _mode: FileMode
    _reader: ReaderType | None
    _writer: WriterType | None
    _metaproxy: MetadataProxy | None
    _metadata_handler: MetadataHandler | None
    _open: bool

    def __init__(
            self,
            name: str,
            slot_type: SlotType,
            description: SlotDescription,
            mode: FileMode,
            reader: ReaderType = None,
            writer: WriterType = None,
            metadata_handler: MetadataHandler | None = None
    ) -> None:
        self._name = name
        self._type = slot_type
        self._description = description
        self._mode = mode
        self._reader = reader
        self._writer = writer

        if self._type is SlotType.INPUT and self._writer is not None:
            raise ValueError(f"A 'writer' parameter is defined for INPUT slot '{self._name}'. "
                             f"Did you mean to define a 'reader' instead?")
        if self._type in (SlotType.OUTPUT, SlotType.RETURN) and self._reader is not None:
            raise ValueError(f"A 'reader' parameter is defined for OUTPUT slot '{self._name}'. "
                             f"Did you mean to define a 'writer' instead?")

        backend_class = _select_backend(description)
        self._backend = backend_class(uri=description.uri, mode=mode)

        self._metadata_handler = metadata_handler
        self._metaproxy = None
        self._open = False

    @property
    def file(self) -> IO:
        return self._backend.file

    @property
    def name(self) -> str:
        return self._name

    @property
    def media_type(self) -> str:
        return self._description.mediatype

    @property
    def meta(self) -> MetadataProxy | None:
        """Return a proxy object to access metadata.

        Returns:
            `None` if the current implementation does not provide access to metadata.
            Otherwise, a `MetadataProxy` is returned. The proxy provides the data, if available,
             but will delay creation of new data until it is actually used.
        """
        return self._metaproxy

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # close the file, but push to remote destination only if there was no exception
        self.close(sync=exc_type is None)

    def open(self):
        if not self._open:
            if self._type == SlotType.INPUT:
                self._backend.pull()
            self._backend.open()
            self._open = True
            self._get_metadata()

    def _get_metadata(self):
        # Read metadata from the handler
        if self._metadata_handler:
            # If metadata is available, use it, otherwise initialize with empty Metadata
            metadata = self._metadata_handler.get(self._description)
            read_only = self._type == SlotType.INPUT
            self._metaproxy = MetadataProxy(metadata=metadata or Metadata(), _readonly=read_only)
        else:
            # If the current environment does not provide any means of metadata handling, create an empty stub
            self._metaproxy = MetadataProxy(metadata=Metadata(), _readonly=True)

    def close(self, sync: bool = True):
        if self._open:
            self._backend.close()
            self._open = False
            if sync and self._type in (SlotType.OUTPUT, SlotType.RETURN):
                self.push()

    def push(self):
        self._backend.push()
        self._set_metadata()

    def _set_metadata(self):
        # Write the metadata to storage
        if (self._metadata_handler is not None) and self._metaproxy is not None:
            self._metadata_handler.set(self._description, self._metaproxy._metadata)

    def read_data(self) -> Any:
        with self as b:
            if self._reader is not None:
                data = self._reader(b.file)
            else:
                data = b.file.read()
        return data

    def write_data(self, data: Any) -> None:
        with self as b:
            if self._writer is not None:
                self._writer(b.file, data)
            else:
                b.file.write(data)

    def __repr__(self) -> str:
        return f"Slot('{self._name}', type={self._type.name}, uri='{self._description.uri}')"

    def __hash__(self) -> int:
        return hash((self._name, self._description.uri, self._type))

    def __eq__(self, other: 'Slot') -> bool:
        if not isinstance(other, Slot):
            raise TypeError(f"Can not compare {type(self)} object with type {type(other)}!?")
        return (
                self._name == other._name and
                self._description.uri == other._description.uri and
                self._type == other._type
        )

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # Remove the backend; it might contain open file handles
        del state['_backend']
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        backend_class = _select_backend(self._description)
        self._backend = backend_class(uri=self._description.uri, mode=self._mode)


class DataSlot:
    """Manages underlying file access and application of de-/serializer functions."""

    annotation: dataslot
    description: DataSlotDescription
    _metadata_handler: MetadataHandler | None

    _slots: list[Slot]

    def __init__(self, description: DataSlotDescription, annotation: dataslot,
                 metadata_handler: MetadataHandler | None = None):
        """
        Args:
            description: The description send with the job offer
            annotation: The annotation generated by the dataslot decorator
            metadata_handler: `MetadataHandler` object managing access to metadata.
        """
        self.description = description
        self.annotation = annotation
        self._metadata_handler = metadata_handler
        self._check_constraints()
        self._init_slots()

    def _check_constraints(self):
        anno = self.annotation
        descr = self.description

        if (anno.slot_type in (SlotType.INPUT,)) and ('w' in anno.mode):
            warnings.warn(f"Write mode set for INPUT dataslot '{anno.name}'! "
                          f"Did you intent to use read-mode instead?")
        elif (anno.slot_type in (SlotType.OUTPUT, SlotType.RETURN)) and ('r' in anno.mode):
            warnings.warn(f"Write mode set for OUTPUT dataslot '{anno.name}'! "
                          f"Did you intent to use write-mode instead?")

        slot_count = len(descr.slots)
        if slot_count == 0:
            raise ProConDataslotError(f"Dataslot description for '{descr.name}' "
                                      f"does not define any slot locations!")
        if slot_count > 1 and not anno.collection:
            raise ProConDataslotError(f"Dataslot for '{descr.name}' is no collection"
                                      f" but got multiple slot locations!")
        if ((descr.name == RETURN_SLOT_NAME)
                and (anno.slot_type is not SlotType.RETURN)):
            raise ProConDataslotError(f"Reserved name {RETURN_SLOT_NAME} "
                                      f"used for a dataslot that is not of type RETURN!")

    def _init_slots(self):
        for idx, slot_description in enumerate(self.description.slots):
            slot_description.dataslot_name = self.description.name
            slot_description.index = idx
        self._slots = [
            Slot(
                name=f"{slot_description.dataslot_name}[{slot_description.index}]",
                slot_type=self.annotation.slot_type,
                description=slot_description,
                mode=self.annotation.mode,
                writer=self.annotation.writer,
                reader=self.annotation.reader,
                metadata_handler=self._metadata_handler,
            )
            for slot_description in self.description.slots
        ]

    @property
    def slots(self) -> list[Slot]:
        """List of all Slots assigned to this Dataslot."""
        return [s for s in self._slots]

    def __enter__(self) -> Self:
        for slot in self._slots:
            slot.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for slot in self._slots:
            slot.close()

    def __len__(self) -> int:
        return len(self.description.slots)

    def __repr__(self) -> str:
        return f"DataSlot('{self.description.name}', type={self.annotation.slot_type.name})"

    # Todo: maybe allow hashing in the future; description and annotation are currently not hashable
    # def __hash__(self):
    #     return hash((self.description, self.annotation))

    def __eq__(self, other: "DataSlot"):
        if not isinstance(other, DataSlot):
            raise TypeError(f"Can not compare {type(self)} object with type {type(other)}!?")
        return (
                self.description == other.description and
                self.annotation == other.annotation
        )

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        # Remove Slots as they might contain open file handles
        del state['_slots']
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        # restore self.annotation and self.description
        self.__dict__.update(state)
        self._init_slots()

    def __copy__(self):
        return DataSlot(annotation=self.annotation, description=self.description)

    def copy_with(self, annotation: dataslot):
        """Create a copy of this DataSlot with a new annotation. (e.g. change the type from INPUT to OUTPUT)"""
        return DataSlot(annotation=annotation, description=self.description)

    def read_data_from_slots(self) -> Union[list[Any], 'DataSlot']:
        """Resolve all files in this dataslot.

        If it is annotated with a type, open the file(s) and apply the configured
        load/deserializer callable.
        """
        if self.annotation.collection:  # multiple Slots
            if not self.annotation.collection_reader:
                raise ProConDataslotError(f"Input-collection-DataSlot '{self.annotation.name}' "
                                          f"has no 'collection_reader' configured!")
            with self:
                read_data = self.annotation.collection_reader(
                    [slot.file for slot in self._slots]
                )
            return read_data

        else:  # single Slot
            if len(self._slots) > 1:
                raise ProConDataslotError(f"Configuration error: Non-collection DataSlot "
                                          f"'{self.annotation.name}' with multiple Slots!")
            return self._slots[0].read_data()

    def write_data_to_slots(self, data: Any):
        """Open the file(s) and apply the configured writer/serializer callable.

        NOTE: Writing strings to files in "text-mode" produces different output
         depending on the underlying operating system. Windows wil use CRLF (\r\n) as
         line ending while most others will use CR (\n).

        :param data: Data to write into this dataslot. It is passed on as parameter
        to the configured `writer`.
        """

        if self.annotation.collection:  # multiple Slots
            if not self.annotation.collection_writer:
                raise ProConDataslotError(f"Output-collection-DataSlot '{self.annotation.name}' "
                                          f"has no 'collection_writer' configured!")
            with self:
                self.annotation.collection_writer(
                    [slot.file for slot in self._slots],
                    data
                )
        else:  # single Slot
            if len(self._slots) > 1:
                raise ProConDataslotError(f"Configuration error: Non-collection DataSlot "
                                          f"'{self.annotation.name}' with multiple Slots!")
            self._slots[0].write_data(data)


DataslotTypes = (DataSlot,)


def isdataslot(t: type) -> bool:
    """Return 'true' if a type is one of the Dataslot types."""
    return t in DataslotTypes
