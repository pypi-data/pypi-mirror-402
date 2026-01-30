from typing import Tuple, Callable

from flask import request, Response, jsonify

from ul_api_utils.const import RESPONSE_PROP_OK, RESPONSE_PROP_PAYLOAD, RESPONSE_PROP_ERRORS, MIME__JSON
from ul_api_utils.debug.debugger import Debugger
from ul_api_utils.utils.api_method import ApiMethod


def not_implemented_handler(error: Exception, *, import_name: str, debugger_enabled: Callable[[], bool]) -> Tuple[Response, int]:
    d = Debugger(import_name, debugger_enabled(), ApiMethod(request.method), request.url)

    if MIME__JSON not in request.headers.get('accept', ''):
        return Response('501. Not Implemented'), 501
    return jsonify({
        RESPONSE_PROP_OK: False,
        RESPONSE_PROP_PAYLOAD: None,
        RESPONSE_PROP_ERRORS: [
            {
                "error_type": "not-implemented",
                "error_message": f"{request.method} {request.url}",
            },
        ],
        **(d.render_dict(501) if d is not None else {}),
    }), 501
