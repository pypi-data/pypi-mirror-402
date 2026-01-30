from logging import Logger
from typing import Optional, TYPE_CHECKING


from ul_api_utils.sentry import sentry

if TYPE_CHECKING:
    from sentry_sdk import Scope
    import flask_sqlalchemy


class WorkerContext:

    __slots__ = (
        '_logger',
        '_sentry_scope',
        '_db',
    )

    def __init__(self, *, logger: Logger, sentry_scope: 'Scope', db: Optional['flask_sqlalchemy.SQLAlchemy']) -> None:
        self._logger = logger
        self._sentry_scope = sentry_scope
        self._db = db

    def sentry_capture(self, e: Exception) -> None:
        sentry.capture_exception(e)

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def db(self) -> 'flask_sqlalchemy.SQLAlchemy':
        assert self._db is not None
        return self._db
