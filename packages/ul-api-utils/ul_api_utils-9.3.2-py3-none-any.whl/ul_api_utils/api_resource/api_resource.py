import io
import json
import logging
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import List, Dict, Any, Optional, Tuple, Union, BinaryIO, Mapping, TypeVar, Callable, Set, TYPE_CHECKING

from flask import render_template, request
from pydantic_core import PydanticCustomError
from werkzeug.datastructures import FileStorage

from ul_api_utils.access import GLOBAL_PERMISSION__PUBLIC, PermissionDefinition, GLOBAL_PERMISSION__PRIVATE_RT, GLOBAL_PERMISSION__PRIVATE
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_resource_error_handling import WEB_EXCEPTION_HANDLING_PARAMS__MAP, \
    ProcessingExceptionsParams, WEB_UNKNOWN_ERROR_PARAMS
from ul_api_utils.api_resource.api_resource_fn_typing import ApiResourceFnTyping
from ul_api_utils.api_resource.api_resource_type import ApiResourceType
from ul_api_utils.api_resource.api_response import JsonApiResponse, HtmlApiResponse, FileApiResponse, \
    JsonApiResponsePayload, EmptyJsonApiResponse, \
    RedirectApiResponse, ProxyJsonApiResponse, RootJsonApiResponse, RootJsonApiResponsePayload
from ul_api_utils.conf import APPLICATION_ENV, APPLICATION_JWT_PUBLIC_KEY, APPLICATION_DEBUG
from ul_api_utils.const import REQUEST_HEADER__X_FORWARDED_FOR, \
    RESPONSE_HEADER__WWW_AUTH, OOPS, REQUEST_HEADER__USER_AGENT
from ul_api_utils.errors import ValidationListApiError, AccessApiError, NoResultFoundApiError, PermissionDeniedApiError, \
    SimpleValidateApiError, ValidateApiError, HasAlreadyExistsApiError, AbstractInternalApiError, \
    InvalidContentTypeError
from ul_api_utils.internal_api.internal_api_response import InternalApiResponse
from ul_api_utils.modules.api_sdk_config import ApiSdkConfig
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt, JWT_VERSION
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.api_request_info import ApiRequestInfo


if TYPE_CHECKING:
    from ul_api_utils.api_resource.db_types import TPayloadInputUnion

TPayload = TypeVar('TPayload')


T = TypeVar('T')
TResp = TypeVar('TResp', bound=Union[JsonApiResponsePayload, RootJsonApiResponsePayload[Any]])


class ApiResource:
    __slots__ = (
        '_debugger_enabled',
        '_token',
        '_token_raw',
        '_type',
        '_config',
        '_api_resource_config',
        '_fn_typing',
        '_logger',
        '_headers',
        '_access',
        '_method',
        '_internal_use__files_to_clean',
        '_now',
        '_limiter_enabled',
        '_db_initialized',
    )

    def __init__(
        self,
        *,
        logger: logging.Logger,
        debugger_enabled: bool,
        type: ApiResourceType,
        config: ApiSdkConfig,
        access: PermissionDefinition,
        headers: Mapping[str, str],
        api_resource_config: Optional[ApiResourceConfig] = None,
        fn_typing: ApiResourceFnTyping,
        limiter_enabled: bool,
        db_initialized: bool,
    ) -> None:
        self._debugger_enabled = debugger_enabled
        self._token: Optional[ApiSdkJwt] = None
        self._token_raw: Optional[str] = None
        self._type = type
        self._config = config
        self._api_resource_config = api_resource_config or ApiResourceConfig()
        self._fn_typing = fn_typing
        self._logger = logger

        self._headers = headers
        self._access = access
        self._method = ApiMethod(str(request.method).strip().upper())  # todo: move it in host function
        self._internal_use__files_to_clean: Set[str] = set()
        self._now = datetime.now()
        self._limiter_enabled = limiter_enabled
        self._db_initialized = db_initialized

    def __repr__(self) -> str:
        return f"ApiResource object. Type: {self._type}, Function: {self._fn_typing.fn.__name__}"

    @property
    def debugger_enabled(self) -> bool:
        return self._debugger_enabled

    def mk_tmp_file(
        self,
        suffix: str | None = None,
        prefix: str | None = None,
    ) -> str:
        f = NamedTemporaryFile(suffix=suffix, prefix=prefix)
        f.seek(0)
        name = f.name
        self._internal_use__files_to_clean.add(str(name))
        return name

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def default_response_payload(self) -> Optional[List[Any]]:
        ApiResourceType.API.validate(self._type)
        return None if not self._fn_typing.response_payload_many else []

    @property
    def method(self) -> ApiMethod:
        return self._method

    @property
    def request_files(self) -> Mapping[str, FileStorage]:
        return request.files

    @property
    def request_headers(self) -> Mapping[str, str]:
        return self._headers

    @property
    def request_info(self) -> ApiRequestInfo:
        x_forwarded_for = self._headers.get(REQUEST_HEADER__X_FORWARDED_FOR)
        return ApiRequestInfo(
            user_agent=request.headers.get(REQUEST_HEADER__USER_AGENT, ''),
            ipv4=x_forwarded_for.split(",")[0] if x_forwarded_for else request.remote_addr or '',
        )

    @property
    def auth_token_raw(self) -> str:
        if self._access == GLOBAL_PERMISSION__PUBLIC:
            raise OverflowError('you could not use token in public api method')
        assert self._token_raw is not None
        return self._token_raw

    @property
    def auth_token(self) -> ApiSdkJwt:
        if self._access == GLOBAL_PERMISSION__PUBLIC:
            raise OverflowError('you could not use token in public api method')
        assert self._token is not None
        return self._token

    def _mk_error(self, error_type: str, error_message: str, debug_specific: bool = True) -> Dict[str, str]:
        error_message = error_message if not debug_specific or (self._debugger_enabled or APPLICATION_DEBUG) else OOPS
        return {
            "error_type": error_type,
            "error_message": error_message,
        }

    def response_api_error(self, err: Exception) -> JsonApiResponse[JsonApiResponsePayload]:
        if isinstance(err, ValidationListApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, err.errors)
        if isinstance(err, json.decoder.JSONDecodeError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [self._mk_error("validation-error", 'json decode failed', False)])
        if isinstance(err, PermissionDeniedApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 403, [self._mk_error("permission-error", 'no rights', False)])
        if isinstance(err, AccessApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 401, [self._mk_error("access-error", str(err), False)])
        if isinstance(err, SimpleValidateApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [self._mk_error("validation-error", str(err), False)])
        if isinstance(err, (PydanticCustomError, ValidateApiError)):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [{
                "error_kind": f"value_error.{err.code}",  # type: ignore
                "error_location": err.location,  # type: ignore
                "error_type": "body-validation-error",
                "error_message": f"{err.msg_template}",  # type: ignore
                "error_input": err.input,  # type: ignore
            }])
        if isinstance(err, NoResultFoundApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 404, [
                self._mk_error("validation-error", str(err), False),
            ])
        if isinstance(err, HasAlreadyExistsApiError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [
                self._mk_error("validation-error", str(err) or "Resource already exist", False),
            ])

        if isinstance(err, InvalidContentTypeError):
            return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [
                self._mk_error("validation-error", str(err), False),
            ])

        if self._db_initialized:
            from ul_db_utils.errors.db_filter_error import DBFiltersError
            from ul_db_utils.errors.db_sort_error import DBSortError
            from sqlalchemy.exc import NoResultFound as NoResultFoundError
            if isinstance(err, (DBFiltersError, DBSortError)):
                return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 400, [
                    self._mk_error("query-validation-error", str(err), False),
                ])
            if isinstance(err, NoResultFoundError):
                e = self._mk_error("validation-error", err._message() if err.args else "Resource not found", False)  # type: ignore
                return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 404, [e])

        if self._limiter_enabled:
            from flask_limiter import RateLimitExceeded
            if isinstance(err, RateLimitExceeded):
                return JsonApiResponse._internal_use_response_error(
                    self._fn_typing.response_payload_many,
                    429,
                    [self._mk_error("rate-limit-exceeded", f"request outside of rate limit - {err.limit.limit}", False)],
                )

        return JsonApiResponse._internal_use_response_error(self._fn_typing.response_payload_many, 500, [self._mk_error("system-error", str(err))])

    def _generate_web_error_response(
        self,
        happened_exception: Exception,
        default_status_code: int,
        error_message: str,
        apply_auth_headers: bool = False,
    ) -> HtmlApiResponse:
        if hasattr(happened_exception, "status_code"):
            default_status_code = happened_exception.status_code
        assert self._config.web_error_template is not None  # only for mypy
        response = HtmlApiResponse(
            content=self.render_template(
                self._config.web_error_template,
                {
                    "error_traceback": happened_exception,
                    "error_message": error_message,
                    "status_code": default_status_code,
                },
            ),
            ok=False,
            status_code=default_status_code,
        )
        if apply_auth_headers:
            if self.method != ApiMethod.OPTIONS and self._config.http_auth is not None:
                response.headers[RESPONSE_HEADER__WWW_AUTH] = f'{self._config.http_auth.scheme} realm="{self._config.http_auth.realm}"'
            return response
        return response

    def response_web_error(self, err: Exception) -> HtmlApiResponse:
        if self._config.web_error_template is None:
            return HtmlApiResponse(error=err, content=OOPS, ok=False, status_code=500)

        if self._db_initialized:
            from sqlalchemy.exc import NoResultFound as NoResultFoundError

            WEB_EXCEPTION_HANDLING_PARAMS__MAP[NoResultFoundError] = ProcessingExceptionsParams(default_status_code=404, error_message="Not found")

        error_response_params = WEB_EXCEPTION_HANDLING_PARAMS__MAP.get(type(err), WEB_UNKNOWN_ERROR_PARAMS)

        return self._generate_web_error_response(
            happened_exception=err,
            default_status_code=error_response_params.default_status_code,
            error_message=error_response_params.error_message,
            apply_auth_headers=error_response_params.apply_auth_headers,
        )

    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        return render_template(
            template_name_or_list=template_name,
            **data,
            NOW=self._now,
        )

    def response_template(self, template_name: str, **kwargs: Any) -> HtmlApiResponse:
        ApiResourceType.WEB.validate(self._type)
        return HtmlApiResponse(
            ok=True,
            status_code=200,
            content=self.render_template(template_name, kwargs),
        )

    def response_proxy(self, response: InternalApiResponse[TResp]) -> ProxyJsonApiResponse[TResp]:
        try:
            response.check()
        except AbstractInternalApiError:
            pass
        return ProxyJsonApiResponse(ok=response.ok, status_code=response.status_code, response=response.result_json)

    def response_redirect(self, location: str) -> RedirectApiResponse:
        return RedirectApiResponse(ok=True, location=location)

    def response_file_ok(
        self,
        path_or_file: Union[str, BinaryIO, io.BytesIO],

        mimetype: Optional[str],  # it will be auto-detected by extension if mimetype==None
        as_attachment: bool = False,
        download_name: Optional[str] = None,
        conditional: bool = True,
        etag: Union[bool, str] = True,
        last_modified: Optional[Union[datetime, int, float]] = None,
        max_age: Optional[Union[int, Callable[[Optional[str]], Optional[int]]]] = None,
    ) -> FileApiResponse:
        ApiResourceType.FILE.validate(self._type)
        if isinstance(path_or_file, str) and not os.path.exists(path_or_file):
            raise NoResultFoundApiError(f'file "{path_or_file}" is not exists')
        return FileApiResponse(
            ok=True,
            status_code=200,
            file_path=path_or_file,
            mimetype=mimetype,
            as_attachment=as_attachment,
            download_name=download_name,
            conditional=conditional,
            etag=etag,
            last_modified=last_modified,
            max_age=max_age,
        )

    def response_created_ok(self, payload: 'TPayloadInputUnion', total_count: Optional[int] = None) -> JsonApiResponse[Any]:
        ApiResourceType.API.validate(self._type)
        return JsonApiResponse(
            ok=True,
            total_count=total_count,
            payload=payload,
            status_code=201,
        )

    def response_empty_ok(self) -> EmptyJsonApiResponse:
        return EmptyJsonApiResponse(ok=True, status_code=200)

    def response_root(self, payload: 'TPayloadInputUnion', status_code: int = 200) -> RootJsonApiResponse[Any]:
        ApiResourceType.API.validate(self._type)
        return RootJsonApiResponse(ok=True, status_code=status_code, root=payload)

    def response_ok(self, payload: 'TPayloadInputUnion', total_count: Optional[int] = None) -> JsonApiResponse[Any]:
        return JsonApiResponse(
            ok=True,
            payload=payload,
            total_count=total_count,
            status_code=200,
        )

    def response_deleted_ok(self) -> JsonApiResponse[Any]:
        ApiResourceType.API.validate(self._type)

        return JsonApiResponse(
            ok=True,
            payload=self.default_response_payload,
            total_count=0 if self._fn_typing.response_payload_many else None,
            status_code=200,
        )

    def _internal_use__check_access(self, jwt_token: Optional[Tuple[Optional[str], str]]) -> None:
        assert self._token is None

        if self._access == GLOBAL_PERMISSION__PUBLIC:
            return None

        if jwt_token is None:
            raise AccessApiError('empty token')

        auth_username, auth_token = jwt_token

        try:
            t = ApiSdkJwt.decode(
                token=auth_token,
                username=auth_username,
                certificate=APPLICATION_JWT_PUBLIC_KEY,
            )
        except Exception:  # noqa: B902
            raise AccessApiError('invalid token data')

        if t.version != JWT_VERSION:
            raise AccessApiError('token has invalid version')

        if self._config.jwt_environment_check_enabled and t.env != APPLICATION_ENV:
            raise AccessApiError('token has invalid environment')

        if t.is_expired:
            raise AccessApiError('token is expired')

        if not self._config.permissions_check_enabled:
            self._token = t
            self._token_raw = auth_token
            return None

        if self._config.jwt_validator is not None:
            try:
                jwt_validation_result = self._config.jwt_validator(t)
                if jwt_validation_result is not None and not jwt_validation_result:
                    raise AccessApiError('Permission denied')
            except Exception as e:  # noqa: B902
                raise AccessApiError(str(e))

        if self._access == GLOBAL_PERMISSION__PRIVATE_RT:
            if not t.is_refresh_token:
                raise AccessApiError('invalid token type')
            self._token_raw = auth_token
            self._token = t
            return None

        if not t.is_access_token:
            raise AccessApiError('invalid token type')

        if self._access != GLOBAL_PERMISSION__PRIVATE:
            if self._config.permissions_validator is not None:
                perm_valid_result = self._config.permissions_validator(t, self._access)
                if perm_valid_result is not None and not perm_valid_result:
                    raise PermissionDeniedApiError('no rights to make this action')
            else:
                if not t.has_permission(self._access):
                    raise PermissionDeniedApiError('no rights to make this action')

        self._token_raw = auth_token
        self._token = t
