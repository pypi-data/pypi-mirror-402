import time
import urllib.parse
from json import dumps
from typing import Optional, Dict, Any, Tuple, Callable

import requests
from flask import g
from werkzeug.datastructures import FileStorage

from ul_api_utils.const import REQUEST_HEADER__INTERNAL, RESPONSE_HEADER__AUTHORIZATION, RESPONSE_HEADER__CONTENT_TYPE, INTERNAL_API__DEFAULT_PATH_PREFIX, REQUEST_HEADER__ACCEPT, \
    RESPONSE_PROP_OK, RESPONSE_PROP_STATUS, RESPONSE_PROP_PAYLOAD, RESPONSE_PROP_COUNT, RESPONSE_PROP_TOTAL, RESPONSE_PROP_ERRORS, REQUEST_HEADER__CONTENT_TYPE, \
    REQUEST_HEADER__CONTENT_ENCODING, REQUEST_HEADER__ACCEPT_CONTENT_ENCODING
from ul_api_utils.debug import stat
from ul_api_utils.errors import NotFinishedRequestInternalApiError, ResponseFormatInternalApiError
from ul_api_utils.internal_api.internal_api_check_context import internal_api_check_context_add_response
from ul_api_utils.internal_api.internal_api_response import InternalApiResponse, InternalApiOverriddenResponse
from ul_api_utils.utils.api_encoding import ApiEncoding
from ul_api_utils.utils.api_format import ApiFormat
from ul_api_utils.utils.api_method import ApiMethod, NO_REQUEST_BODY_METHODS
from ul_api_utils.utils.api_path_version import ApiPathVersion
from ul_api_utils.utils.json_encoder import CustomJSONEncoder


def get_or_create_session(testing_mode: bool) -> requests.Session:
    if testing_mode:
        return requests.Session()

    try:
        return g.internal_api_requests_session  # type: ignore
    except AttributeError:
        s = g.internal_api_requests_session = requests.Session()  # type: ignore
        return s


internal_api_registry: Dict[str, 'InternalApi'] = {}


class InternalApi:
    __slots__ = (
        '_path_prefix',
        '_entry_point',
        '_default_auth_token',
        '_auth_method',
        '_override',
        '_testing_mode',
        '_force_content_type',
        '_force_encoding',
    )

    def __init__(
        self,
        entry_point: str,
        *,
        force_content_type: Optional[ApiFormat] = None,
        force_encoding: Optional[ApiEncoding] = None,
        default_auth_token: Optional[str] = None,
        auth_method: str = 'Bearer',
        path_prefix: str = INTERNAL_API__DEFAULT_PATH_PREFIX,
    ) -> None:
        r = urllib.parse.urlparse(entry_point)
        has_path_pref_in_entry_point = not (r.path == '' or r.path == '/')
        assert '?' not in path_prefix, f'restricted symbol "?" was found in path_prefix="{path_prefix}"'
        assert '&' not in path_prefix, f'restricted symbol "&" was found in path_prefix="{path_prefix}"'
        assert r.query == ''
        assert r.fragment == ''
        assert r.scheme in {'http', 'https'}
        assert not has_path_pref_in_entry_point or (has_path_pref_in_entry_point and path_prefix == INTERNAL_API__DEFAULT_PATH_PREFIX)
        self._path_prefix = path_prefix if not has_path_pref_in_entry_point else r.path
        self._entry_point = urllib.parse.urlunparse(r._replace(path=''))
        self._default_auth_token = default_auth_token
        self._auth_method = auth_method
        internal_api_registry[self._entry_point] = self
        self._override: Dict[str, Dict[ApiMethod, Callable[[bool], InternalApiResponse[Any]]]] = dict()
        self._testing_mode = False

        self._force_content_type = force_content_type
        self._force_encoding = force_encoding

    def test_override(
        self,
        method: ApiMethod,
        path: str,
        status_code: int,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        headers: Optional[Dict[str, str]] = None,
        infinite: bool = False,
        response_json: Any,
        insert_std_schema: bool = True,
    ) -> None:
        self._testing_mode = True

        path = v.compile_path(path, self._path_prefix)

        if path not in self._override:
            self._override[path] = dict()

        if method not in self._override[path]:
            if insert_std_schema:
                response_data = {
                    RESPONSE_PROP_OK: 200 >= status_code > 400,
                    RESPONSE_PROP_COUNT: len(response_json) if isinstance(response_json, (list, tuple)) else (1 if response_json is not None else 0),
                    RESPONSE_PROP_TOTAL: len(response_json) if isinstance(response_json, (list, tuple)) else (1 if response_json is not None else 0),
                    RESPONSE_PROP_ERRORS: [],
                    RESPONSE_PROP_STATUS: status_code,
                    RESPONSE_PROP_PAYLOAD: response_json,
                }
            else:
                response_data = response_json
            text = dumps(response_data, cls=CustomJSONEncoder)

            def _override(has_std_schema: bool) -> InternalApiResponse[Any]:
                if not infinite:
                    self._override[path].pop(method)
                resp = InternalApiOverriddenResponse(status_code=status_code, text=text, headers=headers or {})
                return InternalApiResponse(f'{method.value} {path}', resp, has_std_schema, None)

            self._override[path][method] = _override
            return
        raise OverflowError(f'method "{method.value}" has already defined for override path response "{path}"')

    @property
    def default_auth(self) -> Optional[Tuple[str, str]]:
        if self._auth_method is None or self._default_auth_token is None:
            return None
        return self._auth_method, self._default_auth_token

    @property
    def entry_point(self) -> str:
        return self._entry_point

    @property
    def path_prefix(self) -> str:
        return self._path_prefix

    def request_get(  # Explicit params for mypy checking
        self,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        return self.request(
            ApiMethod.GET,
            path,
            v=v,
            q=q,
            private=private,
            access_token=access_token,
            headers=headers,
            has_std_schema=has_std_schema,
        )

    def request_post(  # Explicit params for mypy checking
        self,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        files: Optional[Dict[str, FileStorage]] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        return self.request(
            ApiMethod.POST,
            path,
            v=v,
            q=q,
            json=json,
            files=files,
            private=private,
            access_token=access_token,
            headers=headers,
            has_std_schema=has_std_schema,
        )

    def request_patch(  # Explicit params for mypy checking
        self,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        return self.request(
            ApiMethod.PATCH,
            path,
            v=v,
            q=q,
            json=json,
            private=private,
            access_token=access_token,
            headers=headers,
            has_std_schema=has_std_schema,
        )

    def request_delete(  # Explicit params for mypy checking
        self,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        return self.request(
            ApiMethod.DELETE,
            path,
            v=v,
            q=q,
            json=json,
            private=private,
            access_token=access_token,
            headers=headers,
            has_std_schema=has_std_schema,
        )

    def request_put(  # Explicit params for mypy checking
        self,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        return self.request(
            ApiMethod.PUT,
            path,
            v=v,
            q=q,
            json=json,
            private=private,
            access_token=access_token,
            headers=headers,
            has_std_schema=has_std_schema,
        )

    def request(
        self,
        method: ApiMethod,
        path: str,
        *,
        v: ApiPathVersion = ApiPathVersion.V01,
        q: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        files: Optional[Dict[str, FileStorage]] = None,
        private: bool = True,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        has_std_schema: bool = True,
    ) -> InternalApiResponse[Any]:
        assert isinstance(method, ApiMethod), f'method must be ApiMethod. "{type(method).__name__}" was given'

        path = v.compile_path(path, self._path_prefix)

        if (
            self._testing_mode
            and path in self._override
            and method in self._override[path]
        ):
            return self._override[path][method](has_std_schema)

        started_at = time.perf_counter()
        q = ApiPathVersion.cleanup_q(q)
        url = f'{self._entry_point.rstrip("/")}{path}'

        req_headers = {
            REQUEST_HEADER__INTERNAL: REQUEST_HEADER__INTERNAL,
            REQUEST_HEADER__ACCEPT: ', '.join(ApiFormat.accept_mimes(self._force_content_type)),
            **stat.get_stats_request_headers(),
        }

        if accept_enc := ', '.join(ApiEncoding.accept_mimes(self._force_encoding)):
            req_headers[REQUEST_HEADER__ACCEPT_CONTENT_ENCODING] = accept_enc

        req_headers.update(headers or {})

        data: Optional[bytes] = None
        debug_data: Optional[str] = None
        if json is not None:
            assert method not in NO_REQUEST_BODY_METHODS, f'{method.value} {url} :: must have no body'
            content_type = ApiFormat.JSON if self._force_content_type is None else self._force_content_type
            data = content_type.serialize_bytes(json)

            if stat.collecting_enabled():
                debug_data = (ApiFormat.JSON.serialize_bytes(json) if content_type is not ApiFormat.JSON else data).decode('utf-8')
            req_headers[REQUEST_HEADER__CONTENT_TYPE] = content_type.mime

        if data is not None:
            if self._force_encoding is None:
                pass
                # if len(data) > AUTO_GZIP_THRESHOLD_LENGTH:
                #     data = ApiEncoding.GZIP.encode(data)
                #     req_headers[REQUEST_HEADER__CONTENT_ENCODING] = ApiEncoding.GZIP.mime
            else:
                if self._force_encoding is not ApiEncoding.NONE:
                    data = self._force_encoding.encode(data)
                    req_headers[REQUEST_HEADER__CONTENT_ENCODING] = self._force_encoding.mime

        if private and (access_token or self._default_auth_token):
            req_headers[RESPONSE_HEADER__AUTHORIZATION] = f'Bearer {access_token or self._default_auth_token}'

        response_text = ''
        status_code = None
        internal_stat = []
        error = None
        requests_response = None
        try:
            requests_response = get_or_create_session(self._testing_mode).request(
                method.value,
                url=url,
                files=({name: (fs.filename, fs.stream, fs.content_type, fs.headers) for name, fs in files.items()} if files is not None else None),
                headers=req_headers,
                data=data,
                params=q,
            )

            if self._force_content_type is None:
                self._force_content_type = ApiFormat.MESSAGE_PACK if requests_response.headers.get(RESPONSE_HEADER__CONTENT_TYPE, '') == ApiFormat.MESSAGE_PACK.mime else None

            status_code = requests_response.status_code
        except Exception as e:  # noqa: B902
            error = e

        try:
            if requests_response is not None:
                internal_response: InternalApiResponse[Any] = InternalApiResponse(f'{method} {requests_response.url}', requests_response, has_std_schema, None)

                internal_api_check_context_add_response(internal_response)

                if has_std_schema:
                    response_text = requests_response.text
                    internal_stat = internal_response.internal_use__debug_stats
        except Exception as e:  # noqa: B902
            error = ResponseFormatInternalApiError(str(e))

        if stat.collecting_enabled():
            stat.add_http_request_stat(
                started_at=started_at,
                method=method,
                url=requests_response.url if requests_response else url,
                status_code=status_code,
                internal_stats=internal_stat,
                request=debug_data,
                response=response_text,
            )

        if error:
            raise NotFinishedRequestInternalApiError('request not finished', error)

        return internal_response
