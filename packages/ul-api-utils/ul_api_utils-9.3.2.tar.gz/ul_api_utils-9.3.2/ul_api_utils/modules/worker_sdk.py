import functools
import logging
from datetime import datetime
from typing import TypeVar, Callable, Any, Union, Dict, Optional, Tuple, TYPE_CHECKING

from flask import Flask
from ul_unipipeline.message.uni_message import UniMessage
from ul_unipipeline.worker.uni_worker import UniWorker
from ul_unipipeline.worker.uni_worker_consumer_message import UniWorkerConsumerMessage

from ul_api_utils.conf import APPLICATION_START_DT
from ul_api_utils.modules.intermediate_state import try_init, try_configure
from ul_api_utils.modules.worker_context import WorkerContext
from ul_api_utils.modules.worker_sdk_config import WorkerSdkConfig
from ul_api_utils.resources.socketio import init_socket_io
from ul_api_utils.sentry import sentry

if TYPE_CHECKING:
    import flask_socketio  # type: ignore # lib without mypy stubs
    from ul_db_utils.modules.postgres_modules.db import DbConfig

TI = TypeVar('TI', bound=UniMessage)
TO = TypeVar('TO', bound=UniMessage)


class WorkerSdk:
    __slots__ = (
        '_initialized_flask_name',
        '_config',
        '_db_initialized',
        '_flask_app_cache',
        '_sio',
    )

    def __init__(self, config: WorkerSdkConfig) -> None:
        try_configure(self)
        self._initialized_flask_name: Optional[str] = None
        self._config = config
        self._db_initialized = False
        self._flask_app_cache: Optional[Flask] = None
        self._sio: Optional['flask_socketio.SocketIO'] = None

    @property
    def socket(self) -> 'flask_socketio.SocketIO':
        assert self._sio is not None, "SocketIO client is not configured, try adding SocketIOConfig to your WorkerSdk first."
        return self._sio

    @property
    def _flask_app(self) -> Flask:
        if self._flask_app_cache is not None:
            return self._flask_app_cache

        if not self._initialized_flask_name:
            raise OverflowError('app was not initialized')

        self._flask_app_cache = Flask(import_name=self._initialized_flask_name)

        return self._flask_app_cache

    def init(self, app_name: str, *, db_config: Optional['DbConfig'] = None) -> 'WorkerSdk':
        self._initialized_flask_name = try_init(self, app_name)
        self._sio = init_socket_io(config=self._config.socket_config)
        if db_config is not None:
            from ul_db_utils.utils.waiting_for_postgres import waiting_for_postgres
            self._db_initialized = True
            db_config._init_from_sdk_with_flask(self)
            waiting_for_postgres(db_config.uri)
        return self

    def init_with_flask(self, app_name: str, *, db_config: Optional['DbConfig'] = None) -> Tuple['WorkerSdk', Flask]:
        self.init(app_name, db_config=db_config)
        return self, self._flask_app

    def handle_message(self, log_edges: bool = True) -> Callable[[Callable[[UniWorker[TI, Optional[TO]], WorkerContext, UniWorkerConsumerMessage[TI]], Optional[Union[Optional[TO], Dict[str, Any]]]]], Callable[[UniWorker[TI, Optional[TO]], UniWorkerConsumerMessage[TI]], Optional[Union[Optional[TO], Dict[str, Any]]]]]:  # noqa: E501  # type: ignore
        assert self._initialized_flask_name is not None

        def wrapper(fn: Callable[[UniWorker[TI, Optional[TO]], WorkerContext, UniWorkerConsumerMessage[TI]], Optional[Union[Optional[TO], Dict[str, Any]]]]) -> Callable[[UniWorker[TI, Optional[TO]], UniWorkerConsumerMessage[TI]], Optional[Union[Optional[TO], Dict[str, Any]]]]:  # noqa: E501
            mdl = fn.__module__
            logger = logging.getLogger(mdl)

            @functools.wraps(fn)
            def wr_handle_message(wrk: UniWorker[TI, Optional[TO]], message: UniWorkerConsumerMessage[TI]) -> Optional[Union[Optional[TO], Dict[str, Any]]]:
                worker_name = type(wrk).__name__
                if log_edges:
                    logger.info(f'worker "{worker_name}" handle message :: START :: {message._meta.payload}')
                with self._flask_app.app_context(), sentry.configure_scope() as sentry_scope:
                    sentry_scope.set_tag('app_name', self._initialized_flask_name)
                    sentry_scope.set_tag('app_type', 'worker')
                    sentry_scope.set_tag('app_uptime', f'{(datetime.now() - APPLICATION_START_DT).seconds // 60}s')
                    sentry_scope.set_tag('app_worker_name', type(wrk).__name__)
                    if message.worker_creator:
                        sentry_scope.set_tag('app_worker_creator', message.worker_creator)

                    db_instance = None
                    if self._db_initialized:
                        from ul_db_utils.modules.postgres_modules import db
                        db_instance = db.db

                    ctx = WorkerContext(
                        logger=logger,
                        sentry_scope=sentry_scope,  # type: ignore
                        db=db_instance,
                    )
                    res = fn(wrk, ctx, message)
                    if log_edges:
                        logger.info(f'worker "{worker_name}" handle message :: END :: {res}')
                    return res
            return wr_handle_message
        return wrapper
