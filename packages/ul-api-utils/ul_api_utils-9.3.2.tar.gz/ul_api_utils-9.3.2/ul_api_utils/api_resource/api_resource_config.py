from typing import Optional, Callable, Tuple

from pydantic import ConfigDict, BaseModel

from ul_api_utils.api_resource.api_response import ApiResponse
from werkzeug import Response as BaseResponse


class ApiResourceConfig(BaseModel):
    swagger_group: Optional[str] = None
    swagger_disabled: bool = False
    exc_handler_bad_request: Optional[Callable[[Exception], Optional[ApiResponse]]] = None
    exc_handler_access: Optional[Callable[[Exception], Optional[ApiResponse]]] = None
    exc_handler_endpoint: Optional[Callable[[Exception], Optional[ApiResponse]]] = None
    override_flask_response: Optional[Callable[[Tuple[BaseResponse, int]], Tuple[BaseResponse, int]]] = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )
