from enum import Enum
from typing import List, Optional, Callable, Union

from pydantic import ConfigDict, BaseModel

from ul_api_utils.access import PermissionRegistry, PermissionDefinition
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt
from ul_api_utils.resources.socketio import SocketIOConfig


def join_route_paths(prev_sect: str, next_sect: str) -> str:
    return prev_sect.rstrip('/') + '/' + next_sect.lstrip('/')


class ApiSdkIdentifyTypeEnum(Enum):
    DISABLED = 'DISABLED'
    CLIENT_IP = 'IP'
    JWT_USER_ID = 'JWT_USER_ID'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'


class ApiSdkHttpAuth(BaseModel):
    realm: str = 'Hidden Zone'
    scheme: str = 'Basic'


class ApiSdkFlaskDebuggingPluginsEnabled(BaseModel):
    flask_monitoring_dashboard: bool = False


class ApiSdkConfig(BaseModel):
    service_name: str
    permissions: Optional[Union[Callable[[], PermissionRegistry], PermissionRegistry]] = None
    permissions_check_enabled: bool = True  # GLOBAL CHECK OF ACCESS AND PERMISSIONS ENABLE
    permissions_validator: Optional[Callable[[ApiSdkJwt, PermissionDefinition], bool]] = None

    jwt_validator: Optional[Callable[[ApiSdkJwt], bool]] = None
    jwt_environment_check_enabled: bool = True

    http_auth: Optional[ApiSdkHttpAuth] = None

    static_url_path: Optional[str] = None
    socket_config: Optional[SocketIOConfig] = None
    web_error_template: Optional[str] = None

    rate_limit: Union[str, List[str]] = '100/minute'  # [count (int)] [per|/] [second|minute|hour|day|month|year][s]
    rate_limit_storage_uri: str = ''  # supports url of redis, memcached, mongodb
    rate_limit_identify: Union[ApiSdkIdentifyTypeEnum, Callable[[], str]] = ApiSdkIdentifyTypeEnum.DISABLED  # must be None if disabled

    cache_storage_uri: str = ''  # supports only redis
    cache_default_ttl: int = 60  # seconds

    flask_debugging_plugins: Optional[ApiSdkFlaskDebuggingPluginsEnabled] = None

    api_route_path_prefix: str = '/api'

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )
