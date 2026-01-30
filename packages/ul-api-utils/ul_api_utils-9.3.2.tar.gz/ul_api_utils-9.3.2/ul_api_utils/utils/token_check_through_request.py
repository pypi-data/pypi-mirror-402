from typing import Callable

from ul_api_utils.errors import Client4XXInternalApiError, NotFinishedRequestInternalApiError
from ul_api_utils.internal_api.internal_api import InternalApi
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt


def api_auth_token_check_through_request(auth_internal_api: InternalApi) -> Callable[[ApiSdkJwt], bool]:
    def token_exist_check(token: ApiSdkJwt) -> bool:
        try:
            auth_internal_api.request_get(f"tokens/{token.user_id}").check()
        except (Client4XXInternalApiError, NotFinishedRequestInternalApiError):
            return False
        else:
            return True
    return token_exist_check
