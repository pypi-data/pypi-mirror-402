import logging

from flask import request
from flask_socketio import emit  # type: ignore

from example.conf import sdk


logger = logging.getLogger(__name__)


@sdk.socket.on('connect')
def handle_connect() -> None:
    logger.info("Connected!")
    logger.info("SESSION INFO: " + str(request.sid))  # type: ignore
    emit('message', {"data1": 1, "data": 2}, room=request.sid, broadcast=True)  # type: ignore
