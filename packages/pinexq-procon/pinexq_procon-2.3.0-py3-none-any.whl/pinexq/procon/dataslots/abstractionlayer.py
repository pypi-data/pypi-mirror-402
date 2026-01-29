import enum
import typing
from typing import TYPE_CHECKING, Any, Callable, Final, NewType, TypeVar

from ..core.exceptions import ProConDataslotError
from .annotation import RETURN_SLOT_NAME, dataslot
from .dataslots import DataSlot, DataSlotDescription, SlotType
from .metadata import MetadataHandler


if TYPE_CHECKING:
    from ..step.introspection import FunctionSchema

R = TypeVar('R')
P = NewType('P', dict[str, Any])
F = NewType('F', Callable[[P], R])


# fmt: off
class NotSetYetType(enum.IntEnum):
    token = 0
NOTSET: Final = NotSetYetType.token  # noqa: E305
# fmt: on


class DataslotLayer:
    """Abstraction layer that handles reading and writing from/to storage locations
    and presents them as regular parameters to the wrapped function."""

    _function: F
    _regular_parameters: P | NotSetYetType = NOTSET
    _dataslot_parameters: P | NotSetYetType = NOTSET
    _result: R | NotSetYetType = NOTSET
    _signature: "FunctionSchema"
    _dataslots_in: dict[str, DataSlot]
    _dataslots_out: dict[str, DataSlot]
    _sig_by_alias: dict[str, dataslot]
    _result_slot: DataSlot | None
    _metadata_handler: MetadataHandler | None

    def __init__(
            self,
            function: F,
            parameters: P,
            signature: "FunctionSchema",
            dataslots_in_descr: dict[str, DataSlotDescription],
            dataslots_out_descr: dict[str, DataSlotDescription],
            metadata_handler: MetadataHandler | None = None
    ):
        """

        Args:
            function: A function (potentially) with dataslots for parameters
                or return value.
            parameters: Dictionary with the parameters the function will be
                called with.
            dataslots_in_descr: Dictionary with `DataSlotDescription` objects
                for each input dataslot parameter.
            dataslots_out_descr: Dictionary with `DataSlotDescription` objects
                for all output dataslots. The return value of the function is
                internally defined by the name '__returns__'.
            signature: A `FunctionSchema` object created during the function's
                introspection (optional). If not provided, the introspection will
                be called on the function internally.
            metadata_handler: An optional `MetadataHandler` object uses to access
                metadata from the currently used backend.
        """
        self._function = function
        self._regular_parameters = parameters or {}  # avoid parameters being None
        self._metadata_handler = metadata_handler

        self._signature = signature
        # Dataslots are presented to the outside by their alias name
        self._sig_by_alias = {(s.alias or s.name): s for n, s in self._signature.dataslots.items()}

        self._dataslots_in = self._init_dataslots(dataslots_in_descr)

        # filter out special output slot `__returns__` (if present) since it isn't part of the function's parameters
        output_slots = self._init_dataslots(dataslots_out_descr)
        self._result_slot = None
        for alias_name, ds in output_slots.items():
            if ds.annotation.name == RETURN_SLOT_NAME:
                self._result_slot = ds
                output_slots.pop(alias_name)
                break
        self._dataslots_out = output_slots

    def _init_dataslots(self, dataslot_description: dict[str, DataSlotDescription]) -> dict[str, DataSlot]:
        """Creates the actual `DataSlot` object and match parameter alias names with
        dataslots from the signature."""
        slots = {}
        for name, descr in dataslot_description.items():
            try:
                slots[name] = DataSlot(
                    description=descr,
                    annotation=self._sig_by_alias[name],
                    metadata_handler=self._metadata_handler,
                )
            except KeyError as ex:
                raise ProConDataslotError(
                    f"Dataslot '{name}' not found in function '{self._signature.name}'. "
                    f"Possibly a typo or the Dataslot is renamed by an alias? "
                    f"(available dataslots: {list(self._sig_by_alias.keys())})") from ex
        return slots

    def __enter__(self) -> "DataslotLayer":
        """Sync all files in the dataslots; i.e. if not local, get them"""
        self._resolve_parameters()
        return self

    def _resolve_parameters(self):
        """Resolve all implicit dataslots.
        If a dataslot is NOT defined as type `Dataslot`, open it and deserialize the data if necessary"""
        self._dataslot_parameters = typing.cast(P, {})
        for n, ds in (self._dataslots_in | self._dataslots_out).items():
            param_name = self._sig_by_alias[n].name
            self._dataslot_parameters[param_name] = self._extract_parameter(ds)

        self._check_for_disjoint_names()

    def _extract_parameter(self, ds: DataSlot) -> Any:
        # Function parameter is explicitly annotated with ":DataSlot"
        if ds.annotation.dtype is DataSlot:
            return ds
        elif ds.annotation.slot_type == SlotType.INPUT:
            return ds.read_data_from_slots()
        elif ds.annotation.slot_type == SlotType.OUTPUT:
            return self._init_output_dataslot_parameter(ds)
        else:
            raise Exception("Tried to init a return dataslot as parameter.")

    def _check_for_disjoint_names(self):
        dataslot_names = set(self._dataslot_parameters.keys())
        parameter_names = set(self._regular_parameters.keys())
        if not dataslot_names.isdisjoint(parameter_names):
            raise ProConDataslotError("Name collision between dataslot- and parameter-names!"
                                      "The following names appear in both: "
                                      f"{', '.join(dataslot_names & parameter_names)}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync all files in the dataslots; i.e. if not local, push them to their destination"""
        # Skip syncing return-Dataslots when there was an Exception, as the function did not return anything.
        # Sync all other Dataslots, even in case of an error.
        if exc_type is None:
            self._resolve_result()
        # self._resolve_result(include_result_slot=exc_type is None)

    def _resolve_result(self, include_result_slot: bool = True):
        """Resolve the result value to a dataslot; i.e. serializing and saving

        Args:
            include_result_slot: Write data for return-Dataslots (default: True)
        """
        if self._result_slot and include_result_slot:
            self._result_slot.write_data_to_slots(self._result)

        for dataslot_name, ds in self._dataslots_out.items():
            if ds.annotation.dtype is not DataSlot:
                ds.write_data_to_slots(self._dataslot_parameters[dataslot_name])

    @property
    def parameters(self) -> P | NotSetYetType:
        """The given parameters and the resolved data from all input dataslots combined."""
        if self._dataslot_parameters is NOTSET:
            return NOTSET
        return typing.cast(
            P, self._regular_parameters | self._dataslot_parameters
        )

    # @property
    # def function(self) -> F:
    #     return self._function

    def call_function(self) -> R:
        """Call the function and return the *raw parameters*."""
        self._result = self._function(
            **self.parameters
        )
        return self._result

    @property
    def result(self) -> R | NotSetYetType:
        """The return value of the function call or None if it was written to an output dataslot"""
        return self._result if not self._result_slot else None

    def has_results_data_slot(self) -> bool:
        """Return True if the function has a `return.dataslot` annotation."""
        return self._result_slot is not None

    @staticmethod
    def _init_output_dataslot_parameter(ds) -> Any:
        """Initialize a dataslot with an empty instance of the annotated type.
        This requires, that the type's constructor can be called without parameter.
        E.g. for `list` calling `list()` will return and empty list."""
        try:
            return ds.annotation.dtype()
        except Exception as ex:
            raise ProConDataslotError(f"Can not create default instance of {ds.annotation.dtype.__name__}"
                                      f" for output dataslot {ds.annotation.name}."
                                      f" Type must be creatable without parameters.") from ex

    def update_parameters(self, new: dict[str, Any]) -> None:
        """Update the internal state of the parameters. Needed to update parameters that use
        "return by reference", i.e. Output-Dataslots, after calling the function."""
        for name, value in new.items():
            if name in self._dataslot_parameters:
                self._dataslot_parameters[name] = value

    def update_result(self, new: Any) -> None:
        """Set the return value of the function. Needed to funnel the return value to a Return-DataSlot."""
        self._result = new

    @property
    def function(self) -> F:
        return self._function
