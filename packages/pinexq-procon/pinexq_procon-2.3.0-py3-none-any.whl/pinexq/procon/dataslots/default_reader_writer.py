from typing import IO, TypeVar, Type
import json

from pydantic import BaseModel

TPydanticBase = TypeVar('TPydanticBase', bound=BaseModel)

class DefaultReaderWriter:
    @staticmethod
    def pydantic_base_writer(filehandle: IO, d: BaseModel):
        filehandle.write(d.model_dump_json(by_alias=True).encode())

    @staticmethod
    def pydantic_base_reader(filehandle: IO, target_type: Type[TPydanticBase]) -> TPydanticBase:
        return target_type.model_validate_json(filehandle.read())

    @staticmethod
    def pydantic_list_base_writer(filehandle: IO, d: list[BaseModel]):
        result = [item.model_dump(by_alias=True) for item in d]
        filehandle.write(json.dumps(result).encode())

    @staticmethod
    def pydantic_list_base_reader(filehandle: IO, target_type: Type[TPydanticBase]) -> list[TPydanticBase]:
        result: list[dict] = json.loads(filehandle.read().decode())
        base_results = [target_type.model_validate(item) for item in result]
        return base_results