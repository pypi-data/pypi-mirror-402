from enum import Enum

from flask_socketio import SocketIO  # type: ignore
from pydantic import BaseModel


class SocketIOConfigType(Enum):
    """
    Defines two basic approaches of creating Socket.IO instance:
        1. SERVER - Socket.IO instance is being attached to the Flask App,
           async gunicorn workers (gevent, eventlet), requires monkey-patching of
           psycopg and default library. Socket application.
        2. EXTERNAL_PROCESS - Socket.IO instance isn't attached to Flask App,
           sync gunicorn workers, doesn't require monkey-patching. Could be any
           API, worker, etc. Used only to submit events from an external process
           to the server clients.

    Further reading: https://flask-socketio.readthedocs.io/en/latest/deployment.html#emitting-from-an-external-process
    """
    SERVER = "SERVER"
    EXTERNAL_PROCESS = "EXTERNAL_PROCESS"


class SocketIOConfig(BaseModel):
    app_type: SocketIOConfigType = SocketIOConfigType.SERVER
    message_queue: str
    channel: str | None = "flask-socketio"
    cors_allowed_origins: str | None = "*"
    logs_enabled: bool | None = False
    engineio_logs_enabled: bool | None = False


class SocketAsyncModesEnum(Enum):
    THREADING = 'threading'
    GEVENT = 'gevent'
    EVENTLET = 'eventlet'
    GEVENT_UWSGI = 'gevent_uwsgi'


def init_socket_io(config: SocketIOConfig | None) -> SocketIO | None:
    socket_io = None
    if config is None:
        return None

    if config.app_type is SocketIOConfigType.SERVER:
        socket_io = SocketIO()

    if config.app_type is SocketIOConfigType.EXTERNAL_PROCESS:
        socket_io = SocketIO(
            message_queue=config.message_queue,
            channel=config.channel,
            logger=config.logs_enabled,
            engineio_logger=config.engineio_logs_enabled,
        )
    return socket_io
