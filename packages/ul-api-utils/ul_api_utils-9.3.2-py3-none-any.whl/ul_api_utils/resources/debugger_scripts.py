import os.path
from typing import TYPE_CHECKING, Optional, List

from pydantic import BaseModel

from ul_api_utils.access import GLOBAL_PERMISSION__PUBLIC
from ul_api_utils.api_resource.api_resource import ApiResource
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_response import FileApiResponse, JsonApiResponse, JsonApiResponsePayload
from ul_api_utils.const import API_PATH__DEBUGGER_JS_UI, API_PATH__DEBUGGER_JS_MAIN, THIS_LIB_CWD
from ul_api_utils.errors import NoResultFoundApiError
from ul_api_utils.internal_api.internal_api import internal_api_registry
from ul_api_utils.utils.api_path_version import ApiPathVersion

if TYPE_CHECKING:
    from ul_api_utils.modules.api_sdk import ApiSdk


class DebuggerExplainBody(BaseModel):
    sql: str
    requests_hierarchy: List[str] = []

    costs: bool = True
    summary: bool = True
    buffers: bool = True
    verbose: bool = False
    # timing: bool = False
    # analyze: bool = True


class DebuggerExplainResponse(JsonApiResponsePayload):
    sql: str
    explanation: Optional[List[str]] = None


def load_debugger_static_scripts(sdk: 'ApiSdk') -> None:
    conf = ApiResourceConfig(swagger_disabled=True)

    # INIT JS File

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_UI, v=ApiPathVersion.NO_PREFIX, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_ui(api_resource: ApiResource) -> FileApiResponse:
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-ui.js'), mimetype='application/javascript')

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_UI, v=ApiPathVersion.NO_VERSION, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_ui_nov(api_resource: ApiResource) -> FileApiResponse:
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-ui.js'), mimetype='application/javascript')

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_UI, v=ApiPathVersion.V01, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_ui_v1(api_resource: ApiResource) -> FileApiResponse:
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-ui.js'), mimetype='application/javascript')

    # MAIN JS File

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_MAIN, v=ApiPathVersion.NO_PREFIX, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_main(api_resource: ApiResource) -> FileApiResponse:
        if not api_resource.debugger_enabled:
            raise NoResultFoundApiError('invalid file path')
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-main.js'), mimetype='application/javascript')

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_MAIN, v=ApiPathVersion.NO_VERSION, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_main_nov(api_resource: ApiResource) -> FileApiResponse:
        if not api_resource.debugger_enabled:
            raise NoResultFoundApiError('invalid file path')
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-main.js'), mimetype='application/javascript')

    @sdk.file_download('GET', API_PATH__DEBUGGER_JS_MAIN, v=ApiPathVersion.V01, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_js_main_v1(api_resource: ApiResource) -> FileApiResponse:
        if not api_resource.debugger_enabled:
            raise NoResultFoundApiError('invalid file path')
        return api_resource.response_file_ok(os.path.join(THIS_LIB_CWD, 'conf', 'ul-debugger-main.js'), mimetype='application/javascript')

    @sdk.rest_api('POST', '/debugger-explain', v=ApiPathVersion.NO_VERSION, access=GLOBAL_PERMISSION__PUBLIC, config=conf)
    def debugger_service_explain(api_resource: ApiResource, body: DebuggerExplainBody) -> JsonApiResponse[DebuggerExplainResponse]:
        if not api_resource.debugger_enabled:
            raise NoResultFoundApiError('invalid file path')

        for req_url in reversed(body.requests_hierarchy):
            for k, api in internal_api_registry.items():
                if req_url.startswith(k):
                    api_body = body.model_dump()
                    api_body['requests_hierarchy'] = []
                    api_result = api.request_post('/debugger-explain', v=ApiPathVersion.NO_VERSION, json=api_body).check().typed(DebuggerExplainResponse)
                    return api_resource.response_ok(api_result.payload)

        from ul_db_utils.modules.postgres_modules.db import db
        options = 'COSTS ' + ('TRUE' if body.costs else 'FALSE')
        options += ', SUMMARY ' + ('TRUE' if body.summary else 'FALSE')
        options += ', VERBOSE ' + ('TRUE' if body.verbose else 'FALSE')
        options += ', BUFFERS ' + ('TRUE' if body.buffers else 'FALSE')

        sql = f'EXPLAIN ({options})\n{body.sql.strip().strip(";").strip()};'

        return api_resource.response_ok(DebuggerExplainResponse(
            sql=sql,
            explanation=[i for i, *_i in db.session.execute(sql).fetchall()]),
        )
