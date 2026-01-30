from enum import Enum
from ul_api_utils.utils.flask_swagger_generator.exceptions import SwaggerGeneratorError


class RequestType(Enum):
    """
    Class RequestType: Enum for types of requests
    """

    POST = 'post'
    GET = 'get'
    DELETE = 'delete'
    PUT = 'put'
    PATCH = 'patch'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def from_string(value: str) -> 'RequestType':

        if isinstance(value, str):

            if value.lower() == 'post':
                return RequestType.POST
            elif value.lower() == 'get':
                return RequestType.GET
            elif value.lower() == 'delete':
                return RequestType.DELETE
            elif value.lower() == 'put':
                return RequestType.PUT
            elif value.lower() == 'patch':
                return RequestType.PATCH
            else:
                raise SwaggerGeneratorError('Could not convert value {} to a request type'.format(value))

        else:
            raise SwaggerGeneratorError("Could not convert non string value to a request type")

    def equals(self, other):  # type: ignore

        if isinstance(other, Enum):
            return self.value == other.value
        else:

            try:
                data_base_type = RequestType.from_string(other)
                return data_base_type == self
            except SwaggerGeneratorError:
                pass

            return other == self.value
