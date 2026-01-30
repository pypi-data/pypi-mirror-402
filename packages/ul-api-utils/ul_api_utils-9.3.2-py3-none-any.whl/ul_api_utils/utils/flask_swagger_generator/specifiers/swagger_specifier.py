from abc import ABC, abstractmethod
from typing import List, Optional

from ul_api_utils.utils.flask_swagger_generator.utils.request_type import RequestType
from ul_api_utils.utils.flask_swagger_generator.utils.security_type import SecurityType


class SwaggerSpecifier(ABC):

    def __init__(self) -> None:
        self.application_name: Optional[str] = None
        self.application_version: Optional[str] = None

    @abstractmethod
    def add_response(self, function_name: str, status_code: int, schema, description: str = ""):  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def add_endpoint(
        self,
        function_name: str,
        path: str,
        request_types: List[RequestType],
        group: Optional[str] = None,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def add_query_parameters(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def add_request_body(self, function_name: str, schema) -> None:  # type: ignore
        raise NotImplementedError()

    @abstractmethod
    def add_security(self, function_name: str, security_type: SecurityType) -> None:
        raise NotImplementedError()

    def set_application_name(self, application_name: str) -> None:
        self.application_name = application_name

    def set_application_version(self, application_version: str) -> None:
        self.application_version = application_version

    @abstractmethod
    def clean(self) -> None:
        pass
