from typing import Any

from flask_socketio import send  # type: ignore

from example.conf import sdk


@sdk.socket.on('json')
def handle_json(json: dict[str, Any]) -> None:
    send(json, json=True)
