import time
from enum import Enum, IntEnum
from typing import List, Callable, Any, Optional, Dict, TYPE_CHECKING, Tuple, NamedTuple, Set, Union

from pydantic import model_validator, ConfigDict, Field, BaseModel, PositiveInt, TypeAdapter
from sqlalchemy.sql import text
from ul_unipipeline.errors import UniError
from ul_unipipeline.modules.uni import Uni

from ul_api_utils.api_resource.api_response import JsonApiResponsePayload
from ul_api_utils.errors import Client4XXInternalApiError, Server5XXInternalApiError
from ul_api_utils.internal_api.internal_api import InternalApi
from ul_api_utils.internal_api.internal_api_response import InternalApiResponse
from ul_api_utils.resources.health_check.const import INTERNAL_API_HEALTH_CHECK_PATH, SERVICE_NAME_DELIMITER

if TYPE_CHECKING:
    import flask_sqlalchemy
    from redis import Redis


class HealthCheckResultStatus(IntEnum):
    OK = 200
    WARN = 400
    HAS_ERRORS = 503

    @property
    def status_code(self) -> int:
        if self is HealthCheckResultStatus.OK:
            return 200
        if self is HealthCheckResultStatus.WARN:
            return 400
        if self is HealthCheckResultStatus.HAS_ERRORS:
            return 503
        raise NotImplementedError()


THandlerReturn = Tuple[HealthCheckResultStatus, str, List['HealthCheckResult']]


class HealthCheckStepType(Enum):
    COMMON_CHECK = "COMMON_CHECK"
    INTERNAL_API_CHECK = "INTERNAL_API_CHECK"
    MESSAGE_QUEUE_CHECK = "MESSAGE_QUEUE_CHECK"
    INTERNAL_API_HEALTH_CHECK = "INTERNAL_API_HEALTH_CHECK"

    def _handle_internal_api_check(
        self,
        fn: Callable[..., InternalApiResponse[JsonApiResponsePayload]],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> THandlerReturn:
        try:
            executed_result = fn(*args, **kwargs)
            executed_result.check()
        except Exception as e:  # noqa: B902
            return HealthCheckResultStatus.HAS_ERRORS, str(e), []
        return HealthCheckResultStatus.OK, '', []

    def _handle_internal_api_health_check(self, fn: Callable[..., InternalApiResponse[JsonApiResponsePayload]], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> THandlerReturn:
        try:
            error = None
            executed_result = fn(*args, **kwargs)
            try:
                executed_result.check()
            except (Client4XXInternalApiError, Server5XXInternalApiError) as e:
                error = e
            payload = TypeAdapter(HealthCheckApiResponse).validate_python(executed_result.payload_raw).checks
            if error:
                if isinstance(error, Client4XXInternalApiError):
                    return HealthCheckResultStatus.WARN, '', payload
                return HealthCheckResultStatus.HAS_ERRORS, '', payload
            return HealthCheckResultStatus.OK, '', payload
        except Exception as e:  # noqa: B902
            return HealthCheckResultStatus.HAS_ERRORS, str(e), []

    def _handle_common_check(self, fn: Callable[..., None], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> THandlerReturn:
        try:
            fn(*args, **kwargs)
        except Exception as e:  # noqa: B902
            return HealthCheckResultStatus.HAS_ERRORS, str(e), []
        return HealthCheckResultStatus.OK, '', []

    def _handle_message_queue_check(self, fn: Callable[..., List['HealthCheckQueueStats']], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> THandlerReturn:
        try:
            queues_stats = fn(*args, **kwargs)
        except Exception as e:  # noqa: B902
            return HealthCheckResultStatus.HAS_ERRORS, str(e), []

        return (
            max(stat.status for stat in queues_stats),
            "".join(f"{stat.info}. \n" for stat in queues_stats),
            [],
        )

    def run(self, fn: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Tuple[HealthCheckResultStatus, str, List['HealthCheckResult']]:
        if self is HealthCheckStepType.COMMON_CHECK:
            return self._handle_common_check(fn, args, kwargs)
        if self is HealthCheckStepType.INTERNAL_API_CHECK:
            return self._handle_internal_api_check(fn, args, kwargs)
        if self is HealthCheckStepType.INTERNAL_API_HEALTH_CHECK:
            return self._handle_internal_api_health_check(fn, args, kwargs)
        if self is HealthCheckStepType.MESSAGE_QUEUE_CHECK:
            return self._handle_message_queue_check(fn, args, kwargs)
        raise NotImplementedError()


class HealthCheckResult(BaseModel):
    name: str = Field(
        ...,
        title="Health check step name",
        description="The health-check contains multiple steps to check, each of the steps gets a name.",
    )
    time_spent: float = Field(
        ...,
        title="Time of execution",
        description="Each health-check step takes some time to be processed, "
                    "tells how much time took code execution for the health-check step.",
    )
    status: HealthCheckResultStatus
    info: Optional[str] = Field(
        None,
        title="Information about health-check step",
        description="Each successful health-check step has a status code "
                    "but each failed have the error description here.",
    )
    type: HealthCheckStepType
    internal_health_check_results: List['HealthCheckResult'] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == HealthCheckResultStatus.OK


def get_general_status(statuses: Set[HealthCheckResultStatus]) -> HealthCheckResultStatus:
    if HealthCheckResultStatus.HAS_ERRORS in statuses:
        return HealthCheckResultStatus.HAS_ERRORS
    if HealthCheckResultStatus.HAS_ERRORS not in statuses and HealthCheckResultStatus.WARN in statuses:
        return HealthCheckResultStatus.WARN
    return HealthCheckResultStatus.OK


class HealthCheckStep(NamedTuple):
    name: str
    type: HealthCheckStepType
    executable: Callable[..., Any]
    executable_args: Tuple[Any, ...] = tuple()
    executable_kwargs: Any = Field(default_factory=lambda: dict())

    def run(self) -> Tuple[HealthCheckResultStatus, float, str, List[HealthCheckResult]]:
        start_time = time.perf_counter()
        status, info, internal_health_check_results = self.type.run(self.executable, self.executable_args, self.executable_kwargs)
        time_spent = time.perf_counter() - start_time
        return status, time_spent, info, internal_health_check_results


class HealthCheckContext:
    def __init__(self, service_name: str, request_service_names: str, db: Optional['flask_sqlalchemy.SQLAlchemy'] = None):
        self._db = db
        self._request_service_names = service_name + SERVICE_NAME_DELIMITER + request_service_names
        self._steps: List[HealthCheckStep] = []

    @property
    def steps(self) -> List[HealthCheckStep]:
        return self._steps

    def add_step(
        self,
        name: str,
        executable: Callable[..., Any],
        type_: HealthCheckStepType = HealthCheckStepType.COMMON_CHECK,
        executable_args: Optional[Tuple[Any, ...]] = None,
        executable_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Registers a health-check step that would be executed automatically when health-check endpoint is called.

        Note:
            The executable provided to this method should not handle any exceptions that might be raised
            because the error handling would be applied later under the hood, when all steps are executed.
            On the contrary, the executable can raise exceptions inside of it as an indicator to the health-check
            that something gone wrong. Also, function should not return any value because it won't be handled.
        """
        if not executable_kwargs:
            executable_kwargs = {}
        if not executable_args:
            executable_args = tuple()
        assert callable(executable), "You should provide a function that performs a step of a health check"
        assert isinstance(executable_kwargs, dict), "Provide keyword arguments to function"
        already_existing_steps = [step.name for step in self._steps]
        assert name not in already_existing_steps, "This step has already been registered"
        self._steps.append(
            HealthCheckStep(
                name=name,
                type=type_,
                executable=executable,
                executable_args=executable_args,
                executable_kwargs=executable_kwargs,
            ),
        )

    def check_internal_api_route(
        self,
        internal_api: InternalApi,
        name: str,
        path: str,
        *,
        private: bool = True,
        has_std_schema: bool = True,
        q: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        kind: HealthCheckStepType = HealthCheckStepType.INTERNAL_API_CHECK,
    ) -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish Internal Api checks from other custom checks.

        Note:
            Supports only GET calls to Internal Api.
            If you want your health-check step to perform other
            methods you might need to add it here but its arguable
            that you expect this behavior from health-check.

        Parameters:
            internal_api: Instance of self_api (internal_api) that can be found in project configuration.
            name: The name of the health-check step, f.e. "All BS are online" or "GET devices".
            path: The endpoint that you want to call through internal api, f.e. "/devices/info".
            private: Private or not.
            has_std_schema: Has schema or not.
            q: Query parameters for the internal api GET request.
            access_token: Token to access the internal_api endpoint, usually should use _default_auth_token.
            headers: Headers for the request.
            kind: Type of the check.
        """
        self.add_step(
            name=name,
            type_=kind,
            executable=internal_api.request_get,
            executable_args=(path,),
            executable_kwargs={
                "private": private,
                "has_std_schema": has_std_schema,
                "q": q,
                "access_token": access_token,
                "headers": headers,
            },
        )

    def check_internal_api_health(self, internal_api: InternalApi, name: str) -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish self-api health-check from other custom checks.
        """
        self.check_internal_api_route(
            internal_api,
            name,
            kind=HealthCheckStepType.INTERNAL_API_HEALTH_CHECK,
            path=INTERNAL_API_HEALTH_CHECK_PATH,
            q={"service_names": self._request_service_names},
        )

    def check_database_connection_exists(self) -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish database connection check from other custom checks.
        """
        if self._db is None:
            raise NotImplementedError("This function should not be used in a health-check of a service, "
                                      f"that doesn't have db connection, {self._db=}")
        self.add_step(
            name="Database connection exists",
            type_=HealthCheckStepType.COMMON_CHECK,
            executable=self._db_connection_exists,
        )

    def check_redis_connection_exists(self, redis_client: 'Union[Redis[str], Redis[bytes]]') -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish redis client connection check from other custom checks.
        """
        self.add_step(
            name="Redis connection exists",
            type_=HealthCheckStepType.COMMON_CHECK,
            executable=self._redis_connection_exists,
            executable_args=(redis_client,),
        )

    def check_message_queue_connection_exists(
        self, uni: Uni,
    ) -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish message queue connection check from other custom checks.
        """
        self.add_step(
            name="Message Queue Connection",
            type_=HealthCheckStepType.COMMON_CHECK,
            executable=self._message_queue_connection_exists,
            executable_kwargs={"uni": uni},
        )

    def check_message_queues_health(
        self,
        uni: Uni,
        override_queue_limits: Optional[Dict[str, 'HealthCheckMessageQueueRange']] = None,
    ) -> None:
        """
        Registers a wrapper for add_step but created with purpose
        to distinguish message queue health checks from other custom checks.

        Parameters:
            uni: Instance of Uni class with .dag config, usually can be found in lib.py in every service.
            override_queue_limits: Dictionary that contains queue name as a key, and HealthCheckMessageQueueRange
                                   with attributes **OK** and **WARN** set.
        """
        self.add_step(
            name="Message Queue Checks",
            type_=HealthCheckStepType.MESSAGE_QUEUE_CHECK,
            executable=self._message_queue_count_check,
            executable_kwargs={
                "uni": uni,
                "override_queue_limits": override_queue_limits,
            },
        )

    def _db_connection_exists(self) -> None:
        """Basic SELECT 1 query to check the database connection."""
        if self._db:  # just for mypy
            self._db.session.query(text("1")).from_statement(text("SELECT 1")).all()

    def _redis_connection_exists(self, redis_client: 'Union[Redis[str], Redis[bytes]]') -> None:
        connection = redis_client.ping()
        if not connection:
            raise ConnectionError("Couldn't establish a connection to Redis client.")

    def _message_queue_connection_exists(self, uni: Uni) -> None:
        """Get the broker if success than connection exists."""
        workers = uni.config.workers.values()
        assert workers, "Workers are not set up"
        for wd in uni.config.workers.values():
            broker = uni._mediator.get_broker(wd.broker.name)
            broker.connect()

    @staticmethod
    def _message_queue_count_check(
        uni: Uni,
        override_queue_limits: Optional[Dict[str, 'HealthCheckMessageQueueRange']] = None,
    ) -> List['HealthCheckQueueStats']:
        """
        Retrieves all message broker queues and processing a status for each one of them.
        Checks for typos that could've been coded through **override_queue_limits** parameter.
        By default, it checks message queue health by pending messages and the default configuration is defined
        in HealthCheckMessageQueueRange.
        """
        if override_queue_limits is None:
            override_queue_limits = {}

        queue_stats = []
        available_queues = [wd.topic for wd in uni.config.workers.values()]
        for overriden_queue in override_queue_limits.keys():
            if overriden_queue not in available_queues:
                raise KeyError(f"Can't find queue with name {overriden_queue} in the list of available queues.")

        for wd in uni.config.workers.values():
            broker = uni._mediator.get_broker(wd.broker.name)
            try:
                message_count = broker.get_topic_approximate_messages_count(wd.topic)
            except UniError:
                continue
            if wd.topic in override_queue_limits:
                overriden_queue_limit = override_queue_limits[wd.topic]
            else:
                overriden_queue_limit = HealthCheckMessageQueueRange()
            queue_status = overriden_queue_limit.get_status(message_count=message_count)
            queue_stats.append(HealthCheckQueueStats(message_count=message_count, queue_name=wd.topic, status=queue_status))
        return queue_stats


class HealthCheckApiResponse(JsonApiResponsePayload):
    service_name: str
    checks: List[HealthCheckResult] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class HealthCheckMessageQueueRange(BaseModel):
    """
    Data class that was implemented in order to classify the health of message queues.
    It derives status of message queue by the number of messages the queue has in it.
    Queue classification by default:
      - **OK** if the queue has **0** pending messages
      - **WARN** if the queue has **1-100** pending messages
      - **HAS_ERRORS** if the queue has **more than 100** pending messages
    Note:
        To override the default behavior, please provide attributes (ok, warn).
        Make sure that warn is more than ok.
    """
    ok: PositiveInt = Field(
        0,
        title="Max OK message count",
        description="Maximum number of messages for queue to have in order to be classified with status HEALTHY (200).",
    )
    warn: PositiveInt = Field(
        100,
        title="Max WARN message count",
        description="Maximum number of messages for queue to have in order to be classified with status WARN (400).",
    )

    @model_validator(mode='after')
    def root_validate(self) -> 'HealthCheckMessageQueueRange':
        ok, warn = self.ok, self.warn
        if ok is not None and warn is not None:
            if ok >= warn:
                raise ValueError(f"OK attribute should be less than WARN attribute, but you provided {ok=}, {warn=}")
        return self

    def get_status(self, message_count: int) -> HealthCheckResultStatus:
        if message_count <= self.ok:
            return HealthCheckResultStatus.OK
        if self.ok < message_count <= self.warn:
            return HealthCheckResultStatus.WARN
        return HealthCheckResultStatus.HAS_ERRORS


class HealthCheckQueueStats(BaseModel):
    message_count: int
    queue_name: str
    status: HealthCheckResultStatus

    @property
    def info(self) -> str:
        return f"Queue with name {self.queue_name} has {self.message_count} messages and status {self.status}"


class HealthCheckQueueMessageCountStatus(BaseModel):
    queue_name: str
    message_count_status_map: Dict[range, HealthCheckResultStatus]

    model_config = ConfigDict(arbitrary_types_allowed=True)
