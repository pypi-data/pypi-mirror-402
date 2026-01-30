from typing import Callable, TYPE_CHECKING, List, Tuple

from ul_api_utils.api_resource.api_request import ApiRequestQuery
from ul_api_utils.api_resource.api_resource import ApiResource
from ul_api_utils.api_resource.api_resource_config import ApiResourceConfig
from ul_api_utils.api_resource.api_response import HtmlApiResponse, JsonApiResponse
from ul_api_utils.resources.health_check.const import SERVICE_NAME_DELIMITER
from ul_api_utils.resources.health_check.health_check import HealthCheckContext, HealthCheckStep, HealthCheckResultStatus, HealthCheckResult, HealthCheckApiResponse
from ul_api_utils.resources.health_check.health_check_template import generate_health_check_table
from ul_api_utils.utils.api_method import ApiMethod

if TYPE_CHECKING:
    from ul_api_utils.modules.api_sdk import ApiSdk


class HealthCheckQuery(ApiRequestQuery):
    service_names: str = ''


def run_health_check_steps(steps: List[HealthCheckStep]) -> Tuple[bool, HealthCheckResultStatus, List[HealthCheckResult]]:
    """
    Runs all the health-check steps and populates the result list
    where all results of steps execution are stored.
    Catches all exceptions that are being raised inside health-check steps and writes the exception info
    to the info.
    Also, calculates time of execution of each health-check step.
    """
    results: List[HealthCheckResult] = []
    for step in steps:
        step_status, time_spent, info, payload = step.run()
        results.append(HealthCheckResult(
            type=step.type,
            name=step.name,
            time_spent=time_spent,
            status=step_status,
            info=info,
            internal_health_check_results=payload,
        ))
    result_statuses = set(result.status for result in results)
    ok = any(status != HealthCheckResultStatus.OK for status in result_statuses)
    status = max(result_statuses)
    return ok, status, results


def init_health_check_resource(fn: Callable[[HealthCheckContext], None], *, api_sdk: 'ApiSdk') -> None:
    @api_sdk.html_view(ApiMethod.GET, path="/sys/health-check", access=api_sdk.ACCESS_PUBLIC)
    def health_check_web(api_resource: ApiResource, query: HealthCheckQuery) -> HtmlApiResponse:
        if api_sdk.config.service_name in query.service_names.split(SERVICE_NAME_DELIMITER):
            return HtmlApiResponse(
                ok=True,
                content='',
                status_code=200,
            )

        health_check_context = HealthCheckContext(
            db=api_sdk.db,
            service_name=api_sdk.config.service_name,
            request_service_names=query.service_names,
        )
        fn(health_check_context)
        ok, status, results = run_health_check_steps(health_check_context.steps)

        return HtmlApiResponse(
            ok=ok,
            content=generate_health_check_table(results, api_sdk.config.service_name),
            status_code=status.status_code,
        )

    @api_sdk.rest_api(ApiMethod.GET, path="/health-check", access=api_sdk.ACCESS_PUBLIC, config=ApiResourceConfig(swagger_disabled=True))
    def health_check_api(api_resource: ApiResource, query: HealthCheckQuery) -> JsonApiResponse[HealthCheckApiResponse]:
        if api_sdk.config.service_name in query.service_names.split(SERVICE_NAME_DELIMITER):
            response = api_resource.response_ok(
                HealthCheckApiResponse(
                    service_name=api_sdk.config.service_name,
                ),
                total_count=0,
            )
            response.status_code = 200
            return response

        health_check_context = HealthCheckContext(
            db=api_sdk.db,
            service_name=api_sdk.config.service_name,
            request_service_names=query.service_names,
        )
        fn(health_check_context)
        ok, status, results = run_health_check_steps(health_check_context.steps)

        response = api_resource.response_ok(
            HealthCheckApiResponse(
                service_name=api_sdk.config.service_name,
                checks=results,
            ),
            total_count=len(results),
        )
        response.status_code = status.status_code
        return response
