from dataclasses import dataclass, field
from typing import Any, TypeVar

import pydantic

from ..core.exceptions import ProConException, ProConSchemaValidationError
from ..dataslots import DataSlotDescription, DataslotLayer
from ..dataslots.metadata import MetadataHandler
from .introspection import FunctionSchema, StepClassInfo


@dataclass
class ExecutionContext:
    """Wraps all information to call a function in a Step container"""

    function_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    input_dataslots: dict[str, "DataSlotDescription"] = field(default_factory=dict)
    output_dataslots: dict[str, "DataSlotDescription"] = field(default_factory=dict)
    metadata_handler: MetadataHandler | None = None


ExecutionContextType = TypeVar("ExecutionContextType", bound="ExecutionContext")


class Step:
    _signatures: dict[str, FunctionSchema]
    _context: ExecutionContextType | None = None

    def __init__(self, use_cli=True):
        self._signatures = StepClassInfo(self).get_func_schemas()

        if use_cli:
            # Do the import here to avoid circular imports
            from pinexq.procon.core.cli import cli

            cli.main(
                obj=self,  # This Step object *self* is available as *obj* attribute in the context of each cli command
                auto_envvar_prefix="PROCON",
            )

    def _call(self, context: ExecutionContextType) -> Any:
        """Calls a function from this container"""
        try:
            # Check if this class contains the function?
            function = getattr(self, context.function_name)
            # is it one of the exposed functions?
            signature = self._signatures[context.function_name]
        except (KeyError, AttributeError):
            raise ProConException(
                f"No function with such name: '{context.function_name}'"
            )

        # Connect to the dataslot sources and load the data into parameters
        with DataslotLayer(
            function=function,
            parameters=context.parameters,
            dataslots_in_descr=context.input_dataslots,
            dataslots_out_descr=context.output_dataslots,
            signature=signature,
            metadata_handler=context.metadata_handler,
        ) as ds_handle:
            # Match parameters with the function's signature
            try:
                # The validation may fail when e.g. Enums are used within the
                # parameters. TODO: find a way how to verify nested enums.
                function_parameter_model = signature.get_parameters_model().model_validate(ds_handle.parameters)
            except pydantic.ValidationError as ex:
                raise ProConSchemaValidationError(
                    "Parameters don't match the functions signature!"
                ) from ex

            # Call the function
            self._context = context
            try:
                # Get the parameter model as a dictionary. Unlike .model_dump(), casting
                # it with `dict()` will only convert the root level Basemodel and not
                # any embedded Basemodels.
                function_parameters = dict(function_parameter_model)

                # The actual function call
                result = ds_handle.function(**function_parameters)

                # Update parameters to handle "return-by-reference" via Output-Dataslots
                ds_handle.update_parameters(function_parameters)
                # Update return value to handle Return-Dataslots
                ds_handle.update_result(result)
            except ProConException:
                raise
            except Exception as ex:
                raise ProConException(
                    f"Exception during execution of '{context.function_name}'!"
                ) from ex
            finally:
                self._context = None

            # Match the results signature
            #  But only if there is no return-Dataslot, in which case there is no return value
            # FixMe: Data in the return.dataslot is actually not validated against the signature!
            if not ds_handle.has_results_data_slot():
                try:
                    signature.get_returns_model().model_validate({"value": result})
                except pydantic.ValidationError as ex:
                    raise ProConSchemaValidationError(
                        "The functions return values doesn't match its signature!"
                    ) from ex

            # The result value or None, if a `return.dataslot` is defined
            func_result = ds_handle.result

        return func_result

    @property
    def step_context(self) -> ExecutionContextType | None:
        return self._context

    @property
    def step_signatures(self) -> dict[str, FunctionSchema]:
        return self._signatures
