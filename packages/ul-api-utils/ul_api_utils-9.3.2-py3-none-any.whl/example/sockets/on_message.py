import logging
from typing import Any

from example.conf import sdk


logger = logging.getLogger(__name__)


@sdk.socket.on('message')
def handle_message(data: Any) -> None:
    logger.info('received message: ')
    logger.info(data)
