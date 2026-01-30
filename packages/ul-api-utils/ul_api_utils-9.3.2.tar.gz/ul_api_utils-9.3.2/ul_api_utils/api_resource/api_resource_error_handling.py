from typing import NamedTuple, Dict, Type

from ul_api_utils.errors import PermissionDeniedApiError, AccessApiError, ValidateApiError, \
    Server5XXInternalApiError, Client4XXInternalApiError


class ProcessingExceptionsParams(NamedTuple):
    default_status_code: int
    error_message: str
    apply_auth_headers: bool = False


WEB_EXCEPTION_HANDLING_PARAMS__MAP: Dict[Type[Exception], ProcessingExceptionsParams] = {
    PermissionDeniedApiError: ProcessingExceptionsParams(default_status_code=403, error_message="Access not permitted", apply_auth_headers=True),
    AccessApiError: ProcessingExceptionsParams(default_status_code=401, error_message="Invalid token", apply_auth_headers=True),
    ValidateApiError: ProcessingExceptionsParams(default_status_code=400, error_message="Request validation error"),
    Server5XXInternalApiError: ProcessingExceptionsParams(default_status_code=500, error_message="Server error"),
    Client4XXInternalApiError: ProcessingExceptionsParams(default_status_code=400, error_message="Request validation error"),
}

WEB_UNKNOWN_ERROR_PARAMS = ProcessingExceptionsParams(default_status_code=500, error_message="Unknown error")
