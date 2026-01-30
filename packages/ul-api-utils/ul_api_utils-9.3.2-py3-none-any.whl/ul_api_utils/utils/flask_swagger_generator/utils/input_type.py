from enum import Enum
from typing import Optional

from ul_api_utils.utils.flask_swagger_generator.exceptions import SwaggerGeneratorError


class InputType(Enum):
    """
    Class SwaggerVersion: Enum for types of swagger version
    """

    INTEGER = 'integer'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    STRING = 'string'
    ARRAY = 'array'
    OBJECT = 'object'
    NESTED = 'nested'
    DATE_TIME = 'datetime'
    UUID = 'uuid'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_string(value: str) -> 'InputType':
        type_map = {
            "integer": InputType.INTEGER, "int": InputType.INTEGER,
            "number": InputType.NUMBER, "num": InputType.NUMBER,
            "boolean": InputType.BOOLEAN, "bool": InputType.BOOLEAN,
            "string": InputType.STRING, "str": InputType.STRING,
            "array": InputType.ARRAY, "object": InputType.OBJECT,
            "nested": InputType.NESTED, "datetime": InputType.STRING,
            "uuid": InputType.UUID,
        }

        if isinstance(value, str):
            route_with_arguments_parenthesis = '('
            if route_with_arguments_parenthesis in value:
                value = value.lower().split(route_with_arguments_parenthesis)[0]
            try:
                return type_map[value.lower()]
            except KeyError:
                raise SwaggerGeneratorError(f'Could not convert {value=} to a input type')
        else:
            raise SwaggerGeneratorError("Could not convert non string value to a parameter type")

    def equals(self, other):  # type: ignore

        if isinstance(other, Enum):
            return self.value == other.value
        else:

            try:
                data_base_type = InputType.from_string(other)
                return data_base_type == self
            except SwaggerGeneratorError:
                pass

            return other == self.value

    def get_flask_input_type_value(self) -> Optional[str]:
        if self.value.lower() == 'integer':
            return 'int'
        elif self.value.lower() in 'number':
            return 'num'
        elif self.value.lower() in 'boolean':
            return 'bool'
        elif self.value.lower() in 'string':
            return 'string'
        elif self.value.lower() == 'array':
            return 'array'
        elif self.value.lower() == 'object':
            return 'object'
        elif self.value.lower() == 'uuid':
            return 'uuid'
        return None
