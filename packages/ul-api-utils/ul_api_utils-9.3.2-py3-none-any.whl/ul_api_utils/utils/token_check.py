from typing import Callable, Type, TYPE_CHECKING

from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt


if TYPE_CHECKING:
    from ul_db_utils.model.base_model import BaseModel


def api_auth_token_check(api_auth_model: Type['BaseModel']) -> Callable[[ApiSdkJwt], bool]:
    def token_exist_check(token: ApiSdkJwt) -> bool:
        token_query = api_auth_model.query.filter_by(id=token.user_id, is_alive=True)
        return token_query.first() is not None
    return token_exist_check
