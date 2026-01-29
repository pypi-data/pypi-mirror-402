import dataclasses
import logging
from dataclasses import dataclass, field
from typing import IO, Any, Callable, Literal, TypeAlias

from ..core.types import UNSET, UNSETTYPE
from ..dataslots.datatypes import MediaTypes, SlotType


log = logging.getLogger(__name__)

DATASLOT_ANNOTATION_NAME = "__dataslots__"
RETURN_SLOT_NAME = "__returns__"

FileMode: TypeAlias = Literal["r", "rb", "w", "wb"]
ReaderType: TypeAlias = Callable[[IO], Any]
WriterType: TypeAlias = Callable[[IO, Any], None]
CollectionReaderType: TypeAlias = Callable[[list[IO]], Any]
CollectionWriterType: TypeAlias = Callable[[[IO], Any], None]


def media_type_2_file_mode(media_type: MediaTypes, is_write=False) -> FileMode:
    access_mode = "w" if is_write else "r"
    mapping = {
        MediaTypes.OCTETSTREAM: "b",
        MediaTypes.JSON: "",
        MediaTypes.FORMDATA: "",
        MediaTypes.SIREN: "",
        MediaTypes.XML: "",
        MediaTypes.ZIP: "b",
        MediaTypes.PDF: "b",
        MediaTypes.TEXT: "",
        MediaTypes.HTML: "",
        MediaTypes.CSV: "",
        MediaTypes.SVG: "",
        MediaTypes.PNG: "b",
        MediaTypes.JPEG: "b",
        MediaTypes.BMP: "b",
        MediaTypes.WORKFLOW_DEFINITION: "",
        MediaTypes.WORKFLOW_REPORT: "",
    }
    # if we do not know the mediatype we assume binary
    binary_suffix = mapping.get(media_type, None)
    if binary_suffix is None:
        binary_suffix = "b"
        log.warning(
            f"Unknown media type {media_type} will assume binary format. "
            f"If this does not fit, please set the mode on the dataslot explicitly."
        )
    return access_mode + binary_suffix


@dataclass
class dataslot:
    """Decorator to attach metadata for a dataslot to a function.
    You can use the general Dataslot decorator `@dataslot` to parametrize all possible options
    manually or use the specialized constructors, which offer default settings and only the
    necessary options for every dataslot type.

    The available constructors are:
        - `dataslot.input`
        - `dataslot.output`
        - `dataslot.input_collection`
        - `dataslot.output_collection`
        - `dataslot.returns`
        - `dataslot.returns_collection`

    Attributes:
        name: The name has to match the functions parameter that will be used as dataslot.
        alias: The name for this dataslot presented in the manifest and expected in a job offer.
        title: Brief description of the dataslot.
        description: More detailed description of the dataslot.
        media_type: The media type as `MediaTypes` Enum.
        reader: A callable accepting a file object as parameter and returning the datatype
            expected by the functions' parameter.
        writer: A callable accepting a file object and data to be written as a parameter.
        mode: File mode of the IO object representing the dataslot. Usually set by the constructor
            to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
        dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        collection: Whether the dataslot accepts more than one file as slots. (default: False)
    """

    name: str
    alias: str | None = field(default=None, kw_only=True)
    slot_type: SlotType = field(default=SlotType.INPUT, kw_only=True)
    title: str = field(default_factory=str, kw_only=True)
    description: str = field(default_factory=str, kw_only=True)
    media_type: str = field(default=MediaTypes.OCTETSTREAM, kw_only=True)
    reader: ReaderType | None = field(default=None, kw_only=True)
    writer: WriterType | None = field(default=None, kw_only=True)
    collection_reader: CollectionReaderType | None = field(default=None, kw_only=True)
    collection_writer: CollectionWriterType | None = field(default=None, kw_only=True)
    mode: FileMode = field(default="r", kw_only=True)
    dtype: type | None = field(default=None, kw_only=True)
    collection: bool = field(default=False, kw_only=True)
    min_slots: int | UNSETTYPE = field(default=UNSET, kw_only=True)
    max_slots: int | None | UNSETTYPE = field(default=UNSET, kw_only=True)

    def __post_init__(self):
        if self.min_slots is UNSET:
            self.min_slots = 1
        if self.max_slots is UNSET:
            self.max_slots = self.min_slots
        if (self.max_slots is not None) and (self.min_slots > self.max_slots):
            raise ValueError("Dataslot attribute 'min_slots' has to smaller than 'max_slots'!")

        if (self.collection_reader or self.collection_writer) and not self.collection:
            raise ValueError(
                "'collection_reader' and '*_writer' can only be used for collection-DataSlots"
                " (when the parameter 'collection=True')!"
            )

    @classmethod
    def input(
        cls,
        name: str,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        alias: str | None = None,
        reader: ReaderType | None = None,
        dtype: type | None = None,
    ):
        """Define the parameter `name` as input dataslot.

        Attributes:
            name: The name has to match the functions parameter that will be used as dataslot.
            alias: The name for this dataslot presented in the manifest and expected in a job offer.
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            reader: A callable accepting a file object as parameter and returning the datatype
                expected by the functions' parameter.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        # The typechecker will complain that `_mode` could be None in the return statement below, which can't be.
        _mode = media_type_2_file_mode(media_type, is_write=False) if mode is None else mode
        # Using the following if/else clause it's recognized correctly, even though it's functionally the same.
        # if mode is None:
        #     _mode = media_type_2_file_mode(media_type, is_write=False)
        # else:
        #     _mode = mode
        return cls(
            name,
            slot_type=SlotType.INPUT,
            title=title,
            description=description,
            media_type=media_type,
            mode=_mode,
            alias=alias,
            reader=reader,
            dtype=dtype,
        )

    @classmethod
    def input_collection(
        cls,
        name: str,
        alias: str | None = None,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        collection_reader: CollectionReaderType | None = None,
        dtype: type | None = None,
        min_slots: int | UNSETTYPE = UNSET,
        max_slots: int | None | UNSETTYPE = UNSET,
    ):
        """Define the input dataslot as collection of files

        Attributes:
            name: The name has to match the functions parameter that will be used as dataslot.
            alias: The name for this dataslot presented in the manifest and expected in a job offer.
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        _mode = media_type_2_file_mode(media_type, is_write=False) if mode is None else mode
        return cls(
            name,
            slot_type=SlotType.INPUT,
            collection=True,
            title=title,
            description=description,
            media_type=media_type,
            mode=_mode,  # see comment in input()
            alias=alias,
            collection_reader=collection_reader,
            dtype=dtype,
            min_slots=min_slots,
            max_slots=max_slots,
        )

    @classmethod
    def output(
        cls,
        name: str,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        alias: str | None = None,
        writer: WriterType | None = None,
        dtype: type | None = None,
    ):
        """Define the parameter `name` as output dataslot.

        Attributes:
            name: The name has to match the functions parameter that will be used as dataslot.
            alias: The name for this dataslot presented in the manifest and expected in a job offer.
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            writer: A callable accepting a file object and data to be written as a parameter.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        _mode = media_type_2_file_mode(media_type, is_write=True) if mode is None else mode
        return cls(
            name,
            slot_type=SlotType.OUTPUT,
            title=title,
            description=description,
            media_type=media_type,
            mode=_mode,  # see comment in input()
            alias=alias,
            writer=writer,
            dtype=dtype,
        )

    @classmethod
    def output_collection(
        cls,
        name: str,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        alias: str | None = None,
        collection_writer: CollectionWriterType | None = None,
        dtype: type | None = None,
        min_slots: int | UNSETTYPE = UNSET,
        max_slots: int | None | UNSETTYPE = UNSET,
    ):
        """Define the output dataslot as collection of files

        Attributes:
            name: The name has to match the functions parameter that will be used as dataslot.
            alias: The name for this dataslot presented in the manifest and expected in a job offer.
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        _mode = media_type_2_file_mode(media_type, is_write=True) if mode is None else mode
        return cls(
            name,
            slot_type=SlotType.OUTPUT,
            collection=True,
            title=title,
            description=description,
            media_type=media_type,
            mode=_mode,  # see comment in input()
            alias=alias,
            collection_writer=collection_writer,
            dtype=dtype,
            min_slots=min_slots,
            max_slots=max_slots,
        )

    @classmethod
    def returns(
        cls,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        writer: WriterType | None = None,
        dtype: type | None = None,
    ):
        """Define the return value of the function to be written to a dataslot.

        Attributes:
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            writer: A callable accepting a file object and data to be written as a parameter.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        _mode = media_type_2_file_mode(media_type, is_write=True) if mode is None else mode
        return cls(
            RETURN_SLOT_NAME,
            slot_type=SlotType.RETURN,
            collection=False,
            title=title,
            description=description,
            media_type=media_type,
            mode=_mode,  # see comment in input()
            writer=writer,
            dtype=dtype,
        )

    @classmethod
    def returns_collection(
        cls,
        title: str = "",
        description: str = "",
        media_type: MediaTypes = MediaTypes.OCTETSTREAM,
        mode: FileMode | None = None,
        collection_writer: CollectionWriterType | None = None,
        dtype: type | None = None,
        min_slots: int | UNSETTYPE = UNSET,
        max_slots: int | None | UNSETTYPE = UNSET,
    ):
        """Define the return value of the function will be written to a return dataslot.

        Attributes:
            title: Brief description of the dataslot.
            description: More detailed description of the dataslot.
            media_type: The media type as `MediaTypes` Enum.
            mode: File mode of the IO object representing the dataslot. Usually set by the constructor
                to a reasonable value ('r' for inputs, 'w' for outputs, 'b' for binary).
            dtype: The annotated type of implicitly defined dataslots. Set by the introspection internally.
        """
        _mode = media_type_2_file_mode(media_type, is_write=True) if mode is None else mode
        return cls(
            RETURN_SLOT_NAME,
            slot_type=SlotType.RETURN,
            collection=True,
            title=title,
            description=description,
            mode=_mode,  # see comment in input()
            media_type=media_type,
            collection_writer=collection_writer,
            dtype=dtype,
            min_slots=min_slots,
            max_slots=max_slots,
        )

    # @classmethod
    # def watch(cls, name: str, **kwargs):
    #     """Watch the local filesystem and upload written files to this dataslot."""
    #     raise NotImplementedError()

    def __call__(self, function: Callable[[Any], Any]):
        """Called when used as a decorator to attach metadata to 'func'."""
        metadata = function.__dict__.setdefault(DATASLOT_ANNOTATION_NAME, {})
        if self.name in metadata:
            raise NameError(f"A dataslot with the name '{self.name}' is already defined on '{function.__name__}()'!")
        if (self.name == RETURN_SLOT_NAME) and (self.slot_type is not SlotType.RETURN):
            raise NameError(f"Invalid dataslot name.The name '{RETURN_SLOT_NAME}' is reserved for internal use.")
        metadata[self.name] = self

        return function

    def update(self, d: "dataslot"):
        """Update this dataslot with information from another dataslot"""
        if not isinstance(d, self.__class__):
            raise TypeError("Can only update with dataslots of the same type!")

        fields_with_default_value = {
            f.name  #
            for f in dataclasses.fields(d)
            if getattr(d, f.name) == f.default
        }
        set_fields = {
            name: value  #
            for name, value in dataclasses.asdict(d).items()
            if name not in fields_with_default_value
        }
        return dataclasses.replace(self, **set_fields)

    def __or__(self, other):
        return self.update(other)


def get_dataslot_metadata(function: Callable[[Any], Any]) -> dict[str, dataslot]:
    return getattr(function, DATASLOT_ANNOTATION_NAME, {})
