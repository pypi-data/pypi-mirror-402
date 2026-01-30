import functools
from typing import Tuple, Optional, Callable, Union, List

from flask import request, Response, Flask, jsonify
from jwt import InvalidTokenError

from ul_api_utils.conf import APPLICATION_JWT_PUBLIC_KEY
from ul_api_utils.const import REQUEST_HEADER__X_FORWARDED_FOR, RESPONSE_PROP_OK, RESPONSE_PROP_PAYLOAD, RESPONSE_PROP_ERRORS, MIME__JSON
from ul_api_utils.debug.debugger import Debugger
from ul_api_utils.errors import AccessApiError
from ul_api_utils.modules.api_sdk_config import ApiSdkIdentifyTypeEnum
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt
from ul_api_utils.utils.api_method import ApiMethod


def _rate_limiter_key_ipv4() -> str:
    x_forwarded_for = request.headers.get(REQUEST_HEADER__X_FORWARDED_FOR)
    if x_forwarded_for:
        ip_list = x_forwarded_for.split(",")
        return ip_list[0]
    else:
        return request.remote_addr or 'UNKNOWN'


def _rate_limiter_key_jwt_user_id(get_auth_token: Callable[[], Optional[Tuple[Optional[str], str]]]) -> str:
    token = None
    request_token = get_auth_token()
    if request_token is not None:
        auth_username, auth_token = request_token
        try:
            token = ApiSdkJwt.decode(token=auth_token, username=auth_username, certificate=APPLICATION_JWT_PUBLIC_KEY)
        except (InvalidTokenError, TypeError, AccessApiError):
            # case when token invalid, request rate limited by IP
            return _rate_limiter_key_ipv4()
    return str(token.user_id) if token is not None else _rate_limiter_key_ipv4()


def init_rate_limiter(
    *,
    flask_app: Flask,
    debugger_enabled: Callable[[], bool],
    rate_limit: Union[str, List[str]],
    get_auth_token: Callable[[], Optional[Tuple[Optional[str], str]]],
    identify: Union[ApiSdkIdentifyTypeEnum, Callable[[], str]],
    storage_uri: str,
) -> bool:
    if identify == ApiSdkIdentifyTypeEnum.DISABLED or not storage_uri:
        return False

    from flask_limiter import Limiter, RateLimitExceeded
    if identify == ApiSdkIdentifyTypeEnum.CLIENT_IP:
        identify_func = _rate_limiter_key_ipv4
    elif identify == ApiSdkIdentifyTypeEnum.JWT_USER_ID:
        identify_func = functools.partial(_rate_limiter_key_jwt_user_id, get_auth_token)
    else:
        assert not isinstance(identify, ApiSdkIdentifyTypeEnum)
        identify_func = identify

    @flask_app.errorhandler(429)
    def _rate_lmiter_error_handler(e: RateLimitExceeded) -> Tuple[Response, int]:
        d = Debugger(flask_app.import_name, debugger_enabled(), ApiMethod(request.method), request.url)

        if MIME__JSON not in request.headers.get('accept', ''):
            return Response(f'429. request outside of rate limit - {e.limit.limit}'), 429
        return jsonify({
            RESPONSE_PROP_OK: False,
            RESPONSE_PROP_PAYLOAD: None,
            RESPONSE_PROP_ERRORS: [
                {
                    "error_type": "rate-limit-exceeded",
                    "error_message": f"request outside of rate limit - {e.limit.limit}",
                },
            ],
            **(d.render_dict(429) if d is not None else {}),
        }), 429

    Limiter(
        app=flask_app,
        application_limits=[rate_limit] if isinstance(rate_limit, str) else rate_limit,  # type: ignore
        key_func=identify_func,
        storage_uri=storage_uri,
    )

    return True
