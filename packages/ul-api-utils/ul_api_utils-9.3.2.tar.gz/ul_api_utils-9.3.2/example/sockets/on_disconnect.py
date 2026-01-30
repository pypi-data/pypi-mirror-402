import logging

from flask import request

from example.conf import sdk


logger = logging.getLogger(__name__)


@sdk.socket.on('disconnect')
def disconnect() -> None:
    logger.info("Client disconnected!")
    logger.info("SESSION INFO: " + str(request.sid))  # type: ignore
