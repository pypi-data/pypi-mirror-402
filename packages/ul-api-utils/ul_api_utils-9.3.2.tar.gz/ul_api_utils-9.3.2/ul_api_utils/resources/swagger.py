import os
import re
import sys
import time
from typing import TYPE_CHECKING, NamedTuple, List, Callable

import yaml
from flask import Response, request

from ul_api_utils.access import GLOBAL_PERMISSION__PUBLIC, PermissionDefinition
from ul_api_utils.api_resource.api_resource import ApiResource
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_resource_fn_typing import ApiResourceFnTyping
from ul_api_utils.api_resource.api_resource_type import ApiResourceType
from ul_api_utils.api_resource.api_response import EmptyJsonApiResponse, ApiResponse
from ul_api_utils.conf import APPLICATION_TMP, APPLICATION_DIR, APPLICATION_F, APPLICATION_SWAGGER_PATH, APPLICATION_SWAGGER_SPECIFICATION_PATH
from ul_api_utils.debug.debugger import Debugger, AJAX_INTERSEPTOR
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.api_path_version import ApiPathVersion
from ul_api_utils.utils.flask_swagger_generator.specifiers.swagger_three_specifier import SwaggerThreeSpecifier
from ul_api_utils.utils.flask_swagger_generator.utils.security_type import SecurityType

if TYPE_CHECKING:
    from ul_api_utils.modules.api_sdk import ApiSdk


SLUG_REPLACE_RE = re.compile(r'[^\w\d]+')


class ApiSdkResource(NamedTuple):
    config: ApiResourceConfig
    wrapper_fn: Callable[..., ApiResponse]
    methods: List[ApiMethod]
    path: str
    access: PermissionDefinition
    fn_typing: ApiResourceFnTyping


def load_swagger(sdk: 'ApiSdk', resources: List[ApiSdkResource], api_route_path_prefix: str) -> None:
    flask_app = sdk._flask_app
    swagger_open_api_cache_file = os.path.join(APPLICATION_TMP, f"swagger-{SLUG_REPLACE_RE.sub('_', flask_app.import_name).lower()}-{int(time.time())}.yml")

    from flask_swagger_ui import get_swaggerui_blueprint  # type: ignore

    bp = get_swaggerui_blueprint(
        blueprint_name='swagger_ui',
        base_url=ApiPathVersion.NO_VERSION.compile_path(APPLICATION_SWAGGER_PATH, api_route_path_prefix),
        api_url=ApiPathVersion.NO_VERSION.compile_path(APPLICATION_SWAGGER_SPECIFICATION_PATH, api_route_path_prefix),
    )

    @bp.after_request
    def after_request(response: Response) -> Response:
        d = Debugger(flask_app.import_name, sdk._debugger_enabled_with_pin(), ApiMethod(request.method), request.url)
        if isinstance(response.response, list) and b'<!DOCTYPE html>' in response.response[0]:
            resp = response.get_data(as_text=True)
            resp = resp.replace('</body>', f'{d.render_html(response.status_code)}</body>')
            resp = resp.replace('<head>', f'<head>{AJAX_INTERSEPTOR}')
            response.set_data(resp)
        return response

    flask_app.register_blueprint(bp)

    @sdk.rest_api('GET', APPLICATION_SWAGGER_SPECIFICATION_PATH, v=ApiPathVersion.NO_VERSION, access=GLOBAL_PERMISSION__PUBLIC, config=ApiResourceConfig(swagger_disabled=True))
    def swagger_specification(api_resource: ApiResource) -> EmptyJsonApiResponse:
        try:
            if not os.path.exists(swagger_open_api_cache_file):
                with open(swagger_open_api_cache_file, 'wt') as f:
                    specifier = SwaggerThreeSpecifier()
                    _index_endpoints(specifier, [r for r in resources if APPLICATION_F.has_or_unset(r.access.flags)])
                    specifier.set_application_name('API')
                    specifier.set_application_version('1.0.0')
                    specifier.write(f)
                    specifier.clean()
            with open(swagger_open_api_cache_file, "r") as docs_file:
                swagger_open_api_cache_file_data = docs_file.read()
                docs_object = yaml.load(
                    swagger_open_api_cache_file_data,
                    Loader=yaml.FullLoader,
                )
            return api_resource.response_root(docs_object)
        except OSError:
            return EmptyJsonApiResponse(ok=False, status_code=404)


def _index_endpoints(specifier: SwaggerThreeSpecifier, fn_registry: List[ApiSdkResource]) -> None:
    for resource in fn_registry:
        if resource.fn_typing.api_resource_type == ApiResourceType.WEB:
            continue

        if resource.config.swagger_disabled:
            continue

        fn = resource.fn_typing.fn
        fn_file = os.path.abspath(sys.modules[fn.__module__].__file__)  # type: ignore
        fn_file = os.path.relpath(fn_file, APPLICATION_DIR)  # type: ignore
        group = resource.config.swagger_group or re.sub(r'^.*?/?(?:routes|views)/([^/]+)(?:/.+)?$', r'\1', fn_file[:-len('.py')])

        specifier.add_endpoint(
            function_name=fn.__name__,
            function_object=resource.wrapper_fn,
            path=resource.path,
            request_types=[str(m) for m in resource.methods],
            group=group,
        )

        if resource.fn_typing.body_typing is not None:
            specifier.add_request_body(fn.__name__, resource.fn_typing.get_body_schema())

        response_model = resource.fn_typing.get_return_schema()

        specifier.add_response(
            function_name=fn.__name__,
            status_code=200,
            schema=response_model,
            description=(response_model.__doc__ or '').strip(),
        )

        if resource.access != GLOBAL_PERMISSION__PUBLIC:
            specifier.add_security(fn.__name__, SecurityType.BEARER_AUTH)
