from enum import Enum
from ul_api_utils.utils.flask_swagger_generator.exceptions import SwaggerGeneratorError


class SwaggerVersion(Enum):
    """
    Class SwaggerVersion: Enum for types of swagger version
    """

    VERSION_THREE = 'VERSION_THREE'
    VERSION_TWO = 'VERSION_TWO'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_string(value: str) -> 'SwaggerVersion':
        if isinstance(value, str):
            if value.lower() in ['three', 'version_three']:
                return SwaggerVersion.VERSION_THREE
            elif value.lower() in ['two', 'version_two']:
                return SwaggerVersion.VERSION_TWO
            else:
                raise SwaggerGeneratorError('Could not convert value {} to a swagger version'.format(value))
        else:
            raise SwaggerGeneratorError("Could not convert non string value to a swagger version")

    def equals(self, other):  # type: ignore

        if isinstance(other, Enum):
            return self.value == other.value
        else:

            try:
                data_base_type = SwaggerVersion.from_string(other)
                return data_base_type == self
            except SwaggerGeneratorError:
                pass

            return other == self.value
