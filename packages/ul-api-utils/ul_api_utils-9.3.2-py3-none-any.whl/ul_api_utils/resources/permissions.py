from typing import List, TYPE_CHECKING, Optional, Union, Callable, Any, Dict

from ul_api_utils.access import GLOBAL_PERMISSION__PUBLIC, PermissionRegistry
from ul_api_utils.api_resource.api_resource import ApiResource
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_response import JsonApiResponse, JsonApiResponsePayload
from ul_api_utils.const import API_PATH__PERMISSIONS

if TYPE_CHECKING:
    from ul_api_utils.modules.api_sdk import ApiSdk


class ApiPermissionsResponse(JsonApiResponsePayload):
    category: str
    permissions: List[Dict[str, Any]]
    service: str


def load_permissions(sdk: 'ApiSdk', app_name: str, permissions_registry: Optional[Union[Callable[[], PermissionRegistry], PermissionRegistry]]) -> None:
    @sdk.rest_api('GET', API_PATH__PERMISSIONS, access=GLOBAL_PERMISSION__PUBLIC, config=ApiResourceConfig(swagger_group='system'))
    def permissions(api_resource: ApiResource) -> JsonApiResponse[List[ApiPermissionsResponse]]:
        if permissions_registry is None:
            reg = PermissionRegistry(app_name, 0, 0)
        elif isinstance(permissions_registry, PermissionRegistry):
            reg = permissions_registry
        else:
            reg = permissions_registry()
        resource_permissions = reg.get_categories_with_permissions()
        return api_resource.response_ok(resource_permissions, len(resource_permissions))
