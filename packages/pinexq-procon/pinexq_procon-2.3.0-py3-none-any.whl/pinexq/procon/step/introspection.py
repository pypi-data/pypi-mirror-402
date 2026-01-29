import inspect
from importlib.metadata import version as get_package_version
from types import NoneType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Type

import docstring_parser
import pydantic
from pydantic import Field

from ..core.exceptions import ProConSchemaError
from ..dataslots.annotation import RETURN_SLOT_NAME, SlotType, dataslot, get_dataslot_metadata
from ..dataslots.dataslots import isdataslot
from .schema import DataslotModel, DynamicParameters, DynamicReturns, FunctionModel
from .versioning import get_version_metadata


if TYPE_CHECKING:
    from ..step import Step


class StepClassInfo:
    """Adapter to extract signatures from all methods in a step class."""

    def __init__(self, step: "Step"):
        self.cls = step
        self.funcs = StepClassInfo.funcs_from_cls(step)

    @staticmethod
    def funcs_from_cls(cls: object) -> List[Tuple[str, Callable]]:
        """Return a list with _(name, func)_ for all public functions in _cls_"""
        return [
            (name, f)
            for name, f in inspect.getmembers(cls)
            if not name.startswith("_") and inspect.ismethod(f)
        ]

    def get_func_schemas(self) -> Dict[str, "FunctionSchema"]:
        return {name: FunctionSchema(f) for name, f in self.funcs}


class FunctionSchema:
    """Extract the signature of a given function from its annotations and docstrings"""

    name: str
    function: Callable[[Any], Any]
    version: str

    _docs: docstring_parser.Docstring
    _returns_docs: str
    _param_docs: dict[str, str]
    _param_annotations: dict[str, inspect.Parameter]
    _dataslot_annotations: dict[str, inspect.Parameter]

    _decorator_slots: dict[str, dataslot]
    _parameter_slots: dict[str, dataslot]
    _signature: inspect.Signature

    def __init__(self, function: Callable):
        self.name = function.__name__
        self.function = function
        self.version = str(get_version_metadata(function))
        self._signature = inspect.signature(function)
        self._init_docstrings()
        self._init_decorated_dataslots()
        self._init_annotations()
        self._init_annotated_dataslots()

    def _init_docstrings(self):
        self._docs = docstring_parser.parse(inspect.getdoc(self.function))
        self._param_docs = {p.arg_name: p.description for p in self._docs.params}
        self._returns_docs = self._docs.returns.description if self._docs.returns else ""

    def _init_decorated_dataslots(self):
        # Dataslots defined by function decorator
        self._decorator_slots = get_dataslot_metadata(self.function)

        # Validate for each dataslot that a parameter with that name exists
        decorated_names = set(self._decorator_slots.keys()) - {RETURN_SLOT_NAME}
        parameter_names = set(self._signature.parameters.keys())
        if diff := decorated_names - parameter_names:
            raise ProConSchemaError(
                f"The dataslots {diff} of function '{self.name}' don't match any parameters name!"
            )

        # Update description for the return value with the docstring, if not set in decorator
        if ((RETURN_SLOT_NAME in self._decorator_slots)
                and not self._decorator_slots[RETURN_SLOT_NAME].description):
            self._decorator_slots[RETURN_SLOT_NAME].description = self._returns_docs

    def _init_annotations(self):
        """Get the functions signature and sort between dataslot and "other" parameters."""
        self._dataslot_annotations = {}
        self._param_annotations = {}
        sig = self._signature

        # Check if all parameters and return values have type annotations
        if (any((p.annotation is sig.empty for p in sig.parameters.values()))
            or sig.return_annotation is sig.empty
        ):
            raise ProConSchemaError(
                f"Can not generate schema for function '{self.name}'. Type annotation is missing!"
            )

        # Disallow wildcard `Any` or `object` type annotation
        if (any((p.annotation in (Any, object) for p in sig.parameters.values()))
            or sig.return_annotation in (Any, object)
        ):
            raise ProConSchemaError(
                f"Can not generate schema for function '{self.name}'. "
                f"Wildcard types like `Any` or `object` are not allowed for type annotations!"
            )

        for name, p in sig.parameters.items():
            # Collect all parameters that are by type annotation or function decorator a Dataslot
            if isdataslot(p.annotation) or (name in self._decorator_slots):
                self._dataslot_annotations[name] = p
            # ... everything else are regular parameters.
            self._param_annotations[name] = p

    def _init_annotated_dataslots(self):
        """Create `dataslot` objects for all parameters with a `Dataslot` type annotation."""
        self._parameter_slots = {}
        for name, p in self._dataslot_annotations.items():
            self._parameter_slots[name] = dataslot(
                name=p.name, dtype=p.annotation, description=self._param_docs.get("name", "")
            )

    def _get_parameters_signature(self) -> Dict[str, tuple[Any, Field]]:
        """Returns the parameters annotation combined with their docstring as a dict"""
        params_schema = {}
        for name, p in self._param_annotations.items():
            params_schema[name] = (
                p.annotation,  # parameter type
                Field(
                    title=name,
                    default=p.default if p.default is not p.empty else ...,
                    description=self._param_docs.get(name, None),
                ),
            )
        return params_schema

    def _get_return_signature(self) -> dict[str, tuple[Any, Field]]:
        """Returns the return type combined with its docstring as a dict"""
        return_type = self._signature.return_annotation
        if self._signature.return_annotation in (self._signature.empty, None):
            return_type = NoneType
        returns_schema = {"value": (return_type, Field(..., description=self._returns_docs))}
        return returns_schema

    def get_parameters_model(self, exclude_dataslots: bool = False) -> Type[DynamicParameters]:
        """Function parameters as pydantic model for schema generation"""
        params_signature = self._get_parameters_signature()
        if exclude_dataslots:
            params_signature = {
                n: p for n, p in params_signature.items() if n not in self.dataslots
            }
        return pydantic.create_model("Parameters", __base__=DynamicParameters, **params_signature)

    def get_returns_model(self, exclude_dataslots: bool = False) -> Type[DynamicReturns]:
        """Function's return type as pydantic model for schema generation"""
        if exclude_dataslots and (RETURN_SLOT_NAME in self._decorator_slots):
            returns_signature = {"value": (NoneType, Field(...))}
        else:
            returns_signature = self._get_return_signature()
        return pydantic.create_model("Returns", __base__=DynamicReturns, **returns_signature)

    @property
    def dataslots(self) -> dict[str, dataslot]:
        """Merge all dataslot information from decorators and type annotation"""
        param_ds = self._parameter_slots
        deco_ds = self._decorator_slots
        # Look for a dataslots name in parameters and decorators,
        # if not found create a default dataslot object and merge them.
        dataslot_names = list(self._dataslot_annotations.keys())
        if RETURN_SLOT_NAME in self._decorator_slots:
            dataslot_names.append(RETURN_SLOT_NAME)
        return {
            name: (param_ds.get(name, dataslot(name))).update(deco_ds.get(name, dataslot(name)))
            for name in dataslot_names
        }

    def get_dataslot_models(self) -> tuple[list[DataslotModel], list[DataslotModel]]:
        """Create the signatures for the dataslots"""
        input_dataslots = []
        output_dataslots = []
        for name, d in self.dataslots.items():
            slot_model = DataslotModel(
                name=d.alias or d.name,
                title=d.title,
                description=d.description,
                mediatype=str(d.media_type), # user could use a strenum or similar
                metadata={},
                max_slots=d.max_slots,
                min_slots=d.min_slots,

            )

            if d.slot_type is SlotType.INPUT:
                input_dataslots.append(slot_model)
            else:
                output_dataslots.append(slot_model)
        return input_dataslots, output_dataslots

    @property
    def signature(self) -> dict:
        """Create the functions signature with a parameter list, return type and docstrings"""
        in_ds, out_ds = self.get_dataslot_models()

        return_schema = self.get_returns_model(exclude_dataslots=True).model_json_schema()

        param_schema = None
        p = self.get_parameters_model(exclude_dataslots=True)
        if len(p.model_fields) > 0:
            param_schema = p.model_json_schema()

        fields = dict(
            version=str(self.version),
            function_name=self.name,
            short_description=self._docs.short_description or "",
            long_description=self._docs.long_description or "",
            parameters=param_schema,
            returns=return_schema,
            input_dataslots=[m.model_dump() for m in in_ds],
            output_dataslots=[m.model_dump() for m in out_ds],
            procon_version=get_procon_version(),
        )
        return fields

    def get_function_model(self) -> FunctionModel:
        return FunctionModel(**self.signature)


def get_procon_version() -> str:
    return get_package_version("pinexq-procon")