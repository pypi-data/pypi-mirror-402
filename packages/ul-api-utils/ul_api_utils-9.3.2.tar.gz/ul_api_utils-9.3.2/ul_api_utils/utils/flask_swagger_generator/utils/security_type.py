from enum import Enum
from ul_api_utils.utils.flask_swagger_generator.exceptions import SwaggerGeneratorError


class SecurityType(Enum):
    """
    Class SecurityType: Enum for types of swagger security types
    """

    BEARER_AUTH = 'BEARER_AUTH'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_string(value: str) -> 'SecurityType':

        if isinstance(value, str):

            if value.lower() == 'bearer_auth':
                return SecurityType.BEARER_AUTH
            else:
                raise SwaggerGeneratorError('Could not convert value {} to a security type'.format(value))
        else:
            raise SwaggerGeneratorError("Could not convert non string value to a security type")

    def equals(self, other):  # type: ignore

        if isinstance(other, Enum):
            return self.value == other.value
        else:

            try:
                data_base_type = SecurityType.from_string(other)
                return data_base_type == self
            except SwaggerGeneratorError:
                pass

            return other == self.value
