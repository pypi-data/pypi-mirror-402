from enum import Enum

from ul_api_utils.errors import ResourceRuntimeApiError


class ApiResourceType(Enum):
    WEB = 'web'
    API = 'api'
    FILE = 'file'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    def validate(self, type: 'ApiResourceType') -> None:
        if type is not self:
            raise ResourceRuntimeApiError(f'invalid usage method for api with type {type.value}. only {self.value} are permitted')
