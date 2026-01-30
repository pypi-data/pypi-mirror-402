import functools
import json
import logging
import os
import time
import traceback
from base64 import b64decode
from datetime import datetime
from functools import wraps
from typing import List, Union, Callable, Tuple, Any, Optional, TypeVar, cast, Set, TYPE_CHECKING
from flask import Response, request, Flask, url_for as flask_url_for, g
from pydantic import BaseModel
from redis.connection import parse_url
from ul_py_tool.utils.arg_files_glob import arg_files_print
from werkzeug import Response as BaseResponse
from ul_api_utils.access import PermissionDefinition, GLOBAL_PERMISSION__PRIVATE, GLOBAL_PERMISSION__PRIVATE_RT, \
    GLOBAL_PERMISSION__PUBLIC, PermissionRegistry
from ul_api_utils.api_resource.api_resource import ApiResource
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_resource_fn_typing import ApiResourceFnTyping
from ul_api_utils.api_resource.api_resource_type import ApiResourceType
from ul_api_utils.api_resource.api_response import ApiResponse, JsonApiResponse, RootJsonApiResponse, ProxyJsonApiResponse, AnyJsonApiResponse
from ul_api_utils.conf import APPLICATION_DEBUGGER_PIN, APPLICATION_DEBUG, APPLICATION_DIR, APPLICATION_ENV_IS_LOCAL, APPLICATION_START_DT, APPLICATION_DEBUG_LOGGING
from ul_api_utils.const import REQUEST_HEADER__DEBUGGER, REQUEST_HEADER__INTERNAL
from ul_api_utils.debug import stat
from ul_api_utils.debug.debugger import Debugger
from ul_api_utils.errors import UserAbstractApiError, ResourceRuntimeApiError, ResponseTypeRuntimeApiError
from ul_api_utils.internal_api.internal_api_check_context import internal_api_check_context
from ul_api_utils.modules.api_sdk_config import ApiSdkConfig
from ul_api_utils.modules.intermediate_state import try_init, try_configure
from ul_api_utils.resources.caching import ULCache, TCacheMode, ULCacheMode, ULCacheConfig
from ul_api_utils.resources.debugger_scripts import load_debugger_static_scripts
from ul_api_utils.resources.health_check.health_check import HealthCheckContext
from ul_api_utils.resources.health_check.resource import init_health_check_resource
from ul_api_utils.resources.not_implemented import not_implemented_handler
from ul_api_utils.resources.permissions import load_permissions
from ul_api_utils.resources.rate_limitter import init_rate_limiter
from ul_api_utils.resources.socketio import init_socket_io, SocketAsyncModesEnum, SocketIOConfigType
from ul_api_utils.resources.swagger import load_swagger, ApiSdkResource
from ul_api_utils.sentry import sentry
from ul_api_utils.utils.api_encoding import ApiEncoding
from ul_api_utils.utils.api_method import TMethod, ApiMethod, TMethodShort
from ul_api_utils.utils.api_path_version import ApiPathVersion
from ul_api_utils.utils.cached_per_request import cached_per_request
from ul_api_utils.utils.constants import TKwargs
from ul_api_utils.utils.jinja.t_url_for import t_url_for
from ul_api_utils.utils.jinja.to_pretty_json import to_pretty_json
from ul_api_utils.utils.json_encoder import CustomJSONProvider, SocketIOJsonWrapper
from ul_api_utils.utils.load_modules import load_modules_by_template
from ul_api_utils.utils.uuid_converter import UUID4Converter

if TYPE_CHECKING:
    import flask_socketio  # type: ignore # lib without mypy stubs
    import flask_sqlalchemy
    from flask_mongoengine import MongoEngine      # type: ignore # lib without mypy stubs
    from ul_db_utils.modules.postgres_modules.db import DbConfig
    from ul_db_utils.modules.mongo_db_modules.db import MongoDbConfig

TFn = TypeVar("TFn", bound=Callable[..., ApiResponse])


logger = logging.getLogger(__name__)


def add_files_to_clean(files: Set[str]) -> None:
    if hasattr(g, '_api_utils_files_to_clean'):
        for f in files:
            g._api_utils_files_to_clean.add(f)  # type: ignore
    else:
        g._api_utils_files_to_clean = files  # type: ignore


def clean_files() -> None:
    files: Set[str] = getattr(g, '_api_utils_files_to_clean', set())
    for f in files:
        try:
            os.unlink(f)
        except Exception as e:  # noqa: B902
            logger.warning(f'file {f} deleted before clean :: {e}')
    files.clear()


def _get_error_types(response: ApiResponse) -> Optional[str]:
    if isinstance(response, AnyJsonApiResponse) and isinstance(response.errors, (list, tuple)) and len(response.errors) > 0:
        for err in response.errors:
            err_t = None
            if isinstance(err, BaseModel):  # type: ignore
                err_t = getattr(err, 'error_type', None)  # type: ignore
            elif isinstance(err, dict):
                err_t = err.get('error_type', None)
            if isinstance(err_t, str):
                return err_t
    return None


class ApiSdk:
    ACCESS_PUBLIC = GLOBAL_PERMISSION__PUBLIC
    ACCESS_PRIVATE = GLOBAL_PERMISSION__PRIVATE
    ACCESS_PRIVATE_RT = GLOBAL_PERMISSION__PRIVATE_RT

    __slots__ = (
        '_config',
        '_routes_loaded',
        '_request_started_at',
        '_initialized_flask_name',
        '_templates_dir',
        '_fn_registry',
        '_flask_app_cache',
        '_sio',
        '_limiter_enabled',
        '_cache',
        '_db',
    )

    def __init__(self, config: ApiSdkConfig) -> None:
        try_configure(self)

        self._config = config
        self._routes_loaded = False
        self._request_started_at = time.perf_counter()
        self._initialized_flask_name: Optional[str] = None
        self._flask_app_cache: Optional[Flask] = None
        self._limiter_enabled = False
        self._cache = None
        self._sio: Optional['flask_socketio.SocketIO'] = None
        self._templates_dir = os.path.join(APPLICATION_DIR, 'templates')

        self._fn_registry: List[ApiSdkResource] = []
        self._db: Optional['flask_sqlalchemy.SQLAlchemy'] | Optional['MongoEngine'] = None

    @property
    def config(self) -> ApiSdkConfig:
        return self._config

    @property
    def socket(self) -> 'flask_socketio.SocketIO':
        assert self._sio is not None, "SocketIO is not configured, try adding SocketIOConfig to your ApiSdk first."
        return self._sio

    def init_with_flask(self, app_name: str, *, db_config: Optional['MongoDbConfig'] | Optional['DbConfig'] = None) -> Flask:
        self._initialized_flask_name = try_init(self, app_name)
        self._sio = init_socket_io(config=self._config.socket_config)

        if db_config is not None and type(db_config).__name__ == 'MongoDbConfig':
            from ul_db_utils.utils.waiting_for_mongo import waiting_for_mongo
            from ul_db_utils.modules.mongo_db_modules.db import db
            db_config._init_from_sdk_with_flask(self)
            waiting_for_mongo(db_config.uri)
            self._db = db

        if db_config is not None and type(db_config).__name__ == 'DbConfig':
            from ul_db_utils.utils.waiting_for_postgres import waiting_for_postgres
            from ul_db_utils.modules.postgres_modules.db import db       # yes, db already defined, but can not use two conigs
            db_config._init_from_sdk_with_flask(self)
            waiting_for_postgres(db_config.uri)
            self._db = db

        self._limiter_enabled = init_rate_limiter(
            flask_app=self._flask_app,
            debugger_enabled=self._debugger_enabled_with_pin,
            get_auth_token=self._get_auth_token,
            identify=self._config.rate_limit_identify,
            rate_limit=self._config.rate_limit,
            storage_uri=self._config.rate_limit_storage_uri,
        )
        if self._config.cache_storage_uri:
            cache_config: ULCacheConfig = {
                'CACHE_TYPE': "RedisCache",
                'CACHE_REDIS_HOST': '',
                'CACHE_REDIS_PORT': '',
                'CACHE_REDIS_PASSWORD': '',
                'CACHE_DEFAULT_TIMEOUT': self._config.cache_default_ttl,
                'CACHE_KEY_PREFIX': f'CACHE__{self._config.service_name}',
                'CACHE_SOURCE_CHECK': True,
            }
            try:
                redis_url = parse_url(self._config.cache_storage_uri)
            except ValueError as e:
                logger.error(f'broken redis uri :: {e}')
            else:
                assert all(('host' in redis_url, 'port' in redis_url)), 'missing part of redis uri'
                cache_config['CACHE_REDIS_HOST'] = redis_url['host']
                cache_config['CACHE_REDIS_PORT'] = redis_url['port']
                cache_config['CACHE_REDIS_PASSWORD'] = redis_url.get('password', '')
            self._cache = ULCache(self._flask_app, config=cache_config)     # type: ignore

        route_files, ignored_route_files = load_modules_by_template([
            os.path.join(APPLICATION_DIR, 'routes', 'api_*.py'),
            os.path.join(APPLICATION_DIR, 'routes', '**', 'api_*.py'),
            os.path.join(APPLICATION_DIR, 'views', 'view_*.py'),
            os.path.join(APPLICATION_DIR, 'views', '**', 'view_*.py'),
        ])

        if APPLICATION_DEBUG:
            arg_files_print(1000, route_files, ignored_files=ignored_route_files, name='files loaded')

            if (plugins_config := self.config.flask_debugging_plugins) is not None:
                if plugins_config.flask_monitoring_dashboard:
                    import flask_monitoringdashboard as dashboard  # type: ignore
                    if os.environ.get('FLASK_MONITORING_DASHBOARD_CONFIG'):
                        dashboard.config.init_from(envvar='FLASK_MONITORING_DASHBOARD_CONFIG', log_verbose=True)
                    dashboard.bind(self._flask_app)

        load_permissions(self, self._initialized_flask_name, self._config.permissions)

        load_debugger_static_scripts(self)

        load_swagger(self, self._fn_registry, self._config.api_route_path_prefix)

        return self._flask_app

    @property
    def _flask_app(self) -> Flask:
        if self._flask_app_cache is not None:
            return self._flask_app_cache

        if not self._initialized_flask_name:
            raise OverflowError('app was not initialized')

        flask_app = Flask(
            import_name=self._initialized_flask_name,
            static_url_path=self._config.static_url_path,
            static_folder=os.path.join(APPLICATION_DIR, 'static'),
            template_folder=self._templates_dir,
        )
        self._flask_app_cache = flask_app

        flask_app.json = CustomJSONProvider(flask_app)  # type: ignore

        flask_app.url_map.converters['uuid'] = UUID4Converter

        flask_app.config['DEBUG'] = APPLICATION_ENV_IS_LOCAL and APPLICATION_DEBUG
        flask_app.config['EXPLAIN_TEMPLATE_LOADING'] = False
        flask_app.config['ENV'] = 'development' if APPLICATION_DEBUG else 'production'
        flask_app.config['SECRET_KEY'] = 'some-long-long-secret-only-for-wtforms-string-be-brave-if-you-use-it-on-prod'
        flask_app.config['TEMPLATES_AUTO_RELOAD'] = APPLICATION_DEBUG and APPLICATION_ENV_IS_LOCAL
        flask_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        flask_app.config['JSON_SORT_KEYS'] = False
        flask_app.config['PREFERRED_URL_SCHEME'] = 'http'
        flask_app.config['APPLICATION_ROOT'] = '/'

        flask_app.add_template_filter(to_pretty_json, 'tojson_pretty')
        flask_app.add_template_filter(to_pretty_json, 'to_json_pretty')

        flask_app.add_template_global(t_url_for, 't_url_for')

        flask_app.before_request(self._before_request)
        flask_app.after_request(self._after_request)
        flask_app.teardown_request(self._teardown_request)

        flask_app.errorhandler(404)(functools.partial(
            not_implemented_handler,
            import_name=self._initialized_flask_name,
            debugger_enabled=self._debugger_enabled_with_pin,
        ))

        if self._config.socket_config and self._config.socket_config.app_type is SocketIOConfigType.SERVER:
            assert self._sio  # mypy
            self._sio.init_app(
                flask_app,
                json=SocketIOJsonWrapper,
                message_queue=self._config.socket_config.message_queue,
                async_mode=SocketAsyncModesEnum.GEVENT.value,
                channel=self._config.socket_config.channel,
                cors_allowed_origins=self._config.socket_config.cors_allowed_origins,
                logger=self._config.socket_config.logs_enabled,
                engineio_logger=self._config.socket_config.engineio_logs_enabled,
            )
            load_modules_by_template([os.path.join(APPLICATION_DIR, 'sockets', '*')])

        return flask_app

    @property
    def ul_cache_factory(self) -> Optional['ULCache']:
        return self._cache

    @property
    def db(self) -> Optional['flask_sqlalchemy.SQLAlchemy'] | Optional['MongoEngine']:
        return self._db

    def _before_request(self) -> None:
        stat.mark_request_started()
        stat.collecting_enable(self._debugger_enabled_with_pin() or (APPLICATION_DEBUG and APPLICATION_ENV_IS_LOCAL))

        if encoding := ApiEncoding.from_mime(request.content_encoding):
            request._cached_data = encoding.decode(request.get_data())

    def _after_request(self, response: Response) -> Response:
        assert self._initialized_flask_name is not None
        if APPLICATION_DEBUG and (APPLICATION_DEBUG_LOGGING or APPLICATION_ENV_IS_LOCAL):
            d = Debugger(self._initialized_flask_name, True, ApiMethod(request.method), request.url)
            d.render_console()
            # if not self._debugger_enabled_with_pin() and APPLICATION_ENV_IS_LOCAL and self._debug_internal_request():
        return response

    def _debugger_enabled_with_pin(self) -> bool:
        return request.headers.get(REQUEST_HEADER__DEBUGGER) == APPLICATION_DEBUGGER_PIN or request.cookies.get(REQUEST_HEADER__DEBUGGER, "") == APPLICATION_DEBUGGER_PIN

    def _teardown_request(self, err: Optional[BaseException]) -> None:
        clean_files()

    def _debug_internal_request(self) -> bool:
        return request.headers.get(REQUEST_HEADER__INTERNAL, '') != REQUEST_HEADER__INTERNAL

    def url_for(self, fn_or_str: Union[Callable, str], **kwargs: Any) -> str:  # type: ignore
        assert self._initialized_flask_name is not None
        if not isinstance(fn_or_str, str):
            fn_or_str = fn_or_str.__name__
        return flask_url_for(fn_or_str, **kwargs)

    def file_download(
        self,
        method: TMethod,
        path: str,
        *,
        config: Optional[ApiResourceConfig] = None,
        v: ApiPathVersion = ApiPathVersion.V01,
        access: Optional[PermissionDefinition] = None,
    ) -> Callable[[TFn], TFn]:
        assert isinstance(v, ApiPathVersion)
        path = v.compile_path(path, self._config.api_route_path_prefix)
        return self._wrap(ApiResourceType.FILE, method, path, config, access)

    def html_view(
        self,
        method: TMethod,
        path: str,
        *,
        config: Optional[ApiResourceConfig] = None,
        access: Optional[PermissionDefinition] = None,
    ) -> Callable[[TFn], TFn]:
        return self._wrap(ApiResourceType.WEB, method, path, config, access)

    def health_check(self) -> Callable[[Callable[[HealthCheckContext], None]], None]:
        return functools.partial(init_health_check_resource, api_sdk=self)

    def cache_api(
        self,
        mode: TCacheMode,
        tags: Tuple[str, ...] | str,
        timeout: Optional[int] = None,
        source_check: Optional[bool] = True,
    ) -> Callable[[TFn], TFn]:
        if self.ul_cache_factory is None:
            logger.warning("Cache URI is not configured, cache will not work.")
            return lambda fn: fn
        if ULCacheMode.compile_mode(mode) == ULCacheMode.READ.value:
            return self.ul_cache_factory.cache_read_wrap(tags, timeout, source_check)
        return self.ul_cache_factory.cache_refresh_wrap(tags)

    def rest_api(
        self,
        method: TMethodShort,
        path: str,
        *,
        config: Optional[ApiResourceConfig] = None,
        v: ApiPathVersion = ApiPathVersion.V01,
        access: Optional[PermissionDefinition] = None,
    ) -> Callable[[TFn], TFn]:
        assert isinstance(v, ApiPathVersion)
        path = v.compile_path(path, self._config.api_route_path_prefix)
        return self._wrap(ApiResourceType.API, method, path, config, access)

    def _wrap(
        self,
        api_type: ApiResourceType,
        method: TMethod,
        path: str,
        api_resource_config: Optional[ApiResourceConfig] = None,
        access: Optional[PermissionDefinition] = None,
    ) -> Callable[[TFn], TFn]:
        config = api_resource_config if api_resource_config is not None else ApiResourceConfig()
        assert isinstance(config, ApiResourceConfig), f'config must be ApiResourceConfig. "{type(config).__name__}" was given'
        access = GLOBAL_PERMISSION__PRIVATE if access is None else access

        assert isinstance(access, PermissionDefinition)
        if access not in (GLOBAL_PERMISSION__PRIVATE, GLOBAL_PERMISSION__PUBLIC, GLOBAL_PERMISSION__PRIVATE_RT):
            assert isinstance(self._config.permissions, PermissionRegistry)
            assert self._config.permissions.has(access)

        flask_methods, enum_methods = ApiMethod.compile_methods(method)

        def wrap(fn: TFn) -> TFn:
            assert self._initialized_flask_name is not None, 'app must be initialized'
            assert fn.__module__, 'empty __module__ of function'

            fn_module = fn.__module__
            fn_name = fn.__name__

            logger = logging.getLogger(fn.__module__)

            fn_typing = ApiResourceFnTyping.parse_fn(api_type, enum_methods, fn)

            @wraps(fn)
            def wrapper(**kwargs: TKwargs) -> Tuple[BaseResponse, int]:
                now = time.time()
                assert access is not None  # for mypy
                debugger_enabled = self._debugger_enabled_with_pin()

                api_resource = ApiResource(
                    logger=logger,
                    debugger_enabled=debugger_enabled,
                    access=access,
                    type=fn_typing.api_resource_type,
                    headers=request.headers,
                    config=self._config,
                    api_resource_config=config,
                    fn_typing=fn_typing,
                    limiter_enabled=self._limiter_enabled,
                    db_initialized=self._db is not None,
                )

                assert self._initialized_flask_name is not None  # just for mypy
                d = Debugger(self._initialized_flask_name, debugger_enabled, ApiMethod(request.method), request.url)

                scope_user_id = None
                scope_token_id = None

                res: Optional[Tuple[BaseResponse, int]] = None

                with sentry.configure_scope() as sentry_scope:
                    sentry_scope.set_tag('app_name', self._initialized_flask_name)
                    sentry_scope.set_tag('app_type', 'api')
                    sentry_scope.set_tag('app_uptime', f'{(datetime.now() - APPLICATION_START_DT).seconds // 60}s')
                    sentry_scope.set_tag('app_api_name', fn_name)
                    sentry_scope.set_tag('app_api_access', access.id)

                    try:
                        with internal_api_check_context():
                            result = None

                            if result is None:
                                try:
                                    api_resource._internal_use__check_access(self._get_auth_token())
                                    if access is not GLOBAL_PERMISSION__PUBLIC:
                                        scope_user_id = api_resource.auth_token.user_id
                                        scope_token_id = api_resource.auth_token.id
                                        sentry_scope.set_user({
                                            'id': api_resource.auth_token.user_id,
                                            'username': api_resource.auth_token.username,
                                        })
                                except Exception as e:  # noqa: B902
                                    if config.exc_handler_access is None:
                                        raise
                                    result = config.exc_handler_access(e)

                            if result is None:
                                try:
                                    kwargs = fn_typing.runtime_validate_request_input(ApiMethod(request.method.upper()), kwargs)
                                except Exception as e:  # noqa: B902
                                    if config.exc_handler_bad_request is None:
                                        raise
                                    result = config.exc_handler_bad_request(e)

                            if result is None:
                                try:
                                    result = self._flask_app.ensure_sync(fn)(api_resource, **kwargs)
                                except Exception as e:  # noqa: B902
                                    if config.exc_handler_endpoint is None:
                                        raise
                                    result = config.exc_handler_endpoint(e)

                            if not isinstance(result, ApiResponse):
                                raise ResponseTypeRuntimeApiError(f'invalid type of response. must be instance of ApiResponse. {repr(result)} was given')
                            if isinstance(result, JsonApiResponse):
                                payload, total_count = fn_typing.runtime_validate_api_response_payload(result.payload, result.total_count, quick=False)
                                result.payload = payload
                                result.total_count = total_count
                            elif isinstance(result, RootJsonApiResponse):
                                payload, _1 = fn_typing.runtime_validate_api_response_payload(result.root, 0, quick=False)
                                result.root = payload
                            elif isinstance(result, ProxyJsonApiResponse):
                                fn_typing.runtime_validate_api_proxy_payload(result.response, quick=False)
                            if len(api_resource._internal_use__files_to_clean) > 0:
                                add_files_to_clean(api_resource._internal_use__files_to_clean)
                            res = result.to_flask_response(d), result.status_code
                    except Exception as e:  # noqa: B902
                        tb = traceback.format_exc()
                        if not isinstance(e, UserAbstractApiError):
                            with stat.measure('') as mes:
                                mes.add_error(tb)
                            if APPLICATION_DEBUG or APPLICATION_ENV_IS_LOCAL:  # MAY BE IT SHOULD BE ENABLED BY DEFAULT ?
                                print(tb)  # noqa
                            if not APPLICATION_ENV_IS_LOCAL:
                                sentry.capture_exception(e)
                        if api_resource._type == ApiResourceType.API:
                            result = api_resource.response_api_error(e)
                        elif api_resource._type == ApiResourceType.WEB:
                            result = api_resource.response_web_error(e)
                        elif api_resource._type == ApiResourceType.FILE:
                            result = api_resource.response_api_error(e)
                        else:
                            result = api_resource.response_web_error(  # type: ignore
                                ResourceRuntimeApiError(f'unsupported type "{api_resource._type.value}" of error response'),
                            )
                        res = result.to_flask_response(d), result.status_code
                    sentry_scope.clear()
                if api_resource_config is not None and api_resource_config.override_flask_response is not None:
                    res = api_resource_config.override_flask_response(res)

                ri = api_resource.request_info
                # TODO: add cache hit flag
                logger.info('AUDIT ' + json.dumps({
                    'user_id': str(scope_user_id) if scope_user_id else None,
                    'token_id': str(scope_token_id) if scope_token_id else None,
                    'method': request.method,
                    'url': request.url,
                    'ipv4': ri.ipv4,
                    'user_agent': ri.user_agent,
                    'duration': time.time() - now,
                    'status_code': res[1] if res is not None else 500,
                    'fn_id': fn_name,
                    'fn_mdl': fn_module,
                    'error_code': _get_error_types(result),
                }))

                return res

            assert access is not None  # for mypy
            self._fn_registry.append(ApiSdkResource(
                path=path,
                config=config,
                wrapper_fn=wrapper,  # type: ignore
                methods=enum_methods,
                fn_typing=fn_typing,
                access=access,
            ))

            wrapper = self._flask_app.route(path, methods=flask_methods)(wrapper)

            return cast(TFn, wrapper)
        return wrap

    @cached_per_request('_api_utils__get_auth_token')
    def _get_auth_token(self) -> Optional[Tuple[Optional[str], str]]:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        if not auth_header.startswith('Bearer'):
            value = auth_header.encode('utf-8')
            try:
                _scheme, credentials = value.split(b' ', 1)
                encoded_username, encoded_password = b64decode(credentials).split(b':', 1)
            except (ValueError, TypeError):
                return None
            try:
                return encoded_username.decode('utf-8'), encoded_password.decode('utf-8')
            except UnicodeDecodeError:
                return encoded_username.decode('latin1'), encoded_password.decode('latin1')
            except Exception:  # noqa: B902
                return None
        auth_segm = auth_header.split(" ")
        if len(auth_segm) < 2:
            return None
        return None, auth_segm[1]
