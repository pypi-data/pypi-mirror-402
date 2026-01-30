# Generic library api-utils

> Provides common api-related functionality that can be used across different services.

> Contains all api-related packages as dependencies.
If you need to use some package that is not available in your service, you should add it here.

## Common functionality & Modules
> This section describes some classes or methods that are available for use in all services that use api-utils.

## ApiResource module

### ApiRequestQuery
```python
class ApiRequestQuery(BaseModel):
    sort: Optional[str] = None
    filter: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    page: Optional[int] = None
```
> Provides basic functionality to the API request. 
> 1. Validation of empty values (replaces empty string to null/None) in API requests.
> 2. Pagination if provided.
> 3. Filtering by filter params if provided.
> 4. Sorting by sort params if provided.

> If you want to add some additional by-default behavior to ApiRequestQuery than you have to add it here.

### ApiResource
```python
class ApiResource:
    def __init__(
        self,
        *,
        logger: logging.Logger,
        debugger_enabled: bool,
        type: ApiResourceType,
        config: ApiSdkConfig,
        access: PermissionDefinition,
        headers: Mapping[str, str],
        api_resource_config: Optional[ApiResourceConfig] = None,
        fn_typing: ApiResourceFnTyping,
    ) -> None:
        self._debugger_enabled = debugger_enabled
        self._token: Optional[ApiSdkJwt] = None
        self._token_raw: Optional[str] = None
        self._type = type
        self._config = config
        self._api_resource_config = api_resource_config or ApiResourceConfig()
        self._fn_typing = fn_typing
        self._logger = logger

        self._headers = headers
        self._access = access
        self._method = ApiMethod(str(request.method).strip().upper())  # todo: move it in host function
        self._internal_use__files_to_clean: Set[str] = set()
        self._now = datetime.now()
```
> Provides basic functionality to the API resource. Defines common properties for every API resourse.


| ApiResource properties                             | Desription                                                                                                                                                      |
|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ApiResource.debugger_enabled                       | Returns boolean value indicating that debugger is enabled/disabled.                                                                                             |
| ApiResource.logger                                 | Returns ApiResource logger.                                                                                                                                     |
| ApiResource.method                                 | Returns ApiResource API method (GET, POST, PUT, PATCH, DELETE, OPTIONS).                                                                                        |
| ApiResource.request_files                          | Returns files that are attached to Flask API request.                                                                                                           |
| ApiResource.request_headers                        | Returns request headers that are attached to request.                                                                                                           |
| ApiResource.request_info                           | Returns request information that is attached to request (user-agent, ip).                                                                                       |
| ApiResource.auth_token, ApiResource.auth_token_raw | Returns token or raw token.                                                                                                                                     |


## Internal API module

### Internal API
> Provides *InternalAPI* class with basic functionality to support the requests between internal services.
> Implements a wrapper for all types of requests: GET, POST, PUT, PATCH, DELETE.

### Internal API Response
> Provides *InternalApiResponse* class with basic properties of Response, such as:
> .ok, .total_count, .count, .errors, .payload, 
> .status_code, .result_bytes, .result_text, .result_json.


## API SDK Module
> Provides debugger setup for every service that uses it, useful decorators to build views, etc.
> In order to use it in another service, SDK should be initialized and here an example.
```python
web_sdk = ApiSdk(ApiSdkConfig(
    permissions=your_permissions,
    jwt_validator=your_validator,
    not_found_template=path/to/template,
    rate_limit=your_rate_limit,
    other_params_are_listed_below=please_read_them
))
```
## API SDK Config
> Provides configuration for the API SDK.
```python
class ApiSdkConfig(BaseModel):
    permissions: Optional[Union[Callable[[], PermissionRegistry], PermissionRegistry]] = None
    permissions_check_enabled: bool = True  # GLOBAL CHECK OF ACCESS AND PERMISSIONS ENABLE
    permissions_validator: Optional[Callable[[ApiSdkJwt, PermissionDefinition], bool]] = None

    jwt_validator: Optional[Callable[[ApiSdkJwt], bool]] = None
    jwt_environment_check_enabled: bool = True

    http_auth: Optional[ApiSdkHttpAuth] = None

    static_url_path: Optional[str] = None

    not_found_template: Optional[str] = None

    rate_limit: Union[str, List[str]] = '100/minute'  # [count (int)] [per|/] [second|minute|hour|day|month|year][s]
    rate_limit_storage_uri: str = ''  # supports url of redis, memcached, mongodb
    rate_limit_identify: Union[ApiSdkIdentifyTypeEnum, Callable[[], str]] = ApiSdkIdentifyTypeEnum.DISABLED  # must be None if disabled

    api_route_path_prefix: str = '/api'

    class Config:
        extra = Extra.forbid
        allow_mutation = False
        frozen = True
        arbitrary_types_allowed = True
```

> Also, API SDK provides useful decorators that help to create views (web based, API endpoints, file download endpoints).
```python
@web_sdk.html_view(method, path, access=permission, config=ApiResourceConfig)
@web_sdk.rest_api(method, path, access=permission, config=ApiResourceConfig, v='v1')
```

### Worker SDK
> Provides a useful decorator for message handling that adds logging, Sentry monitoring and WorkerContext.
```python
from src.conf.worker_sdk import worker_sdk

initialized_worker = worker_sdk.init(__name__)


__all__ = (
    'initialized_worker',
)
```
```python
@initialized_worker.handle_message()
def some_worker_function(params):
    ...
```

### Custom Shared Validators
> Library has some commonly-used validators available for use in other services to avoid code duplication.
> If you think that some services will benefit from adding a new one that can be shared, you are welcome.

#### Validate UUID
```python
def validate_uuid4(uuid: Any) -> None:
    try:
        UUID(uuid, version=4)
    except ValueError:
        raise SimpleValidateApiError('invalid uuid')
```

#### Validate empty object
```python
def validate_empty_object(obj_id: str, model: Any) -> Any:
    obj = model.query.filter_by(id=obj_id).first()
    if not obj:
        raise SimpleValidateApiError(f'{model.__name__} data was not found')
    return obj
```

### Custom Exceptions

| Exception                           | Desription                                                                                                                                                      |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AbstractApiError                    | Services can inherit from this error and create own service-oriented API Exceptions. Should not be raised.                                                      |
| AbstractInternalApiError            | Services can inherit from this error and create own service-oriented Internal-API Exceptions. Should not be raised.                                             |
| RequestAbstractInternalApiError     | Services can inherit from this error and create own Exceptions, that should be used before sending a request to another service. Should not be raised.          |
| ResponseAbstractInternalApiError    | Services can inherit from this error and create own Exceptions, that should be used after getting a response from another service. Should not be raised.        |
| ResponseFormatInternalApiError      | Should be raised when the response format from another service is incorrect.                                                                                    |
| ResponseJsonSchemaInternalApiError  | Should be raised when the response schema from another service is incorrect.                                                                                    |
| ResponsePayloadTypeInternalApiError | Should be raised when the response payload types from another services aren't matching.                                                                         |
| Server5XXInternalApiError           | Should be raised when the response status from another service is 5xx. (something wrong at receiving end)                                                       |
| Client4XXInternalApiError           | Should be raised when the response status from another service is 4xx. (something wrong at sender end)                                                          |
| UserAbstractApiError                | Services can inherit from this error and create own Exceptions, that should be used only to stop request handling and only in API-routes. Should not be raised. |
| ValidationListApiError              | Should be raised when the incoming request is invalid because of validation.                                                                                    |
| ValidateApiError                    | Should be raised when the incoming request is invalid because of validation.                                                                                    |
| AccessApiError                      | Should be raised when API-call sender does not have an access to the API.                                                                                       |
| AccessApiError                      | Should be raised when API-call sender do es not have an access to the API.                                                                                      |
| PermissionDeniedApiError            | Should be raised when API-call sender does not have required permissions to access the API.                                                                     |
| NoResultFoundApiError               | Should be raised when we can't return a response because required data does not exist.                                                                          |
| HasAlreadyExistsApiError            | Should be raised when we can't create a new record because the same one already exists.                                                                         |


## Adding new api-related package
> First, try to understand why do you need this library and what exactly can you do with it. Look at the list of
> already existing libraries and think if they can fulfill your needs. 

> Check this library for deprecation, does it have enough maintenance, library dependencies.
> If all above satisfies you, perform next steps:
> 1. Add the package name and version to **Pipfile** under ```[packages]``` section. Example: ```alembic = "==1.8.1"```.
> 2. Run ```pipenv install```.
> 3. Add the package name and version to **setup.py** to ```install-requires``` section.
> 4. Commit changes. ```git commit -m "Add dependency *library-name*"```.
> 5. Run version patch: ```pipenv run version_patch```.
> 6. Push changes directly to dev ```git push origin dev --tags``` or raise MR for your changes to be reviewed.


## Example
```bash
FLASK_DEBUG=1 FLASK_ENV=development FLASK_APP=example.example_app APPLICATION_DIR=$(pwd)/example APPLICATION_DEBUG=1 flask run --port 5001
```

## How to debug using PyCharm Professional:
![debug_example_pycharm.png](debug_example_pycharm.png)


## How to create keys

```bash
pipenv run enc_keys --algorithm=RS256 --service-name some --follower-services foo bar --jwt-permissions-module example.permissions --jwt-user-id 03670a66-fb50-437e-96ae-b42bb83e3d04 --jwt-environment=local
```

```bash
pipenv run enc_keys --algorithm ES256 --service-name some --follower-services foo bar --jwt-permissions-module example.permissions --jwt-user-id 03670a66-fb50-437e-96ae-b42bb83e3d04 --jwt-environment=local
```
