from ul_api_utils.conf import APPLICATION_SENTRY_DSN, APPLICATION_SENTRY_ENABLED_FLASK, DOCKER_BUILD__CONTAINER_CODE_COMMIT_HASH, DOCKER_BUILD__CONTAINER_SERVER_TIME, \
    DOCKER_BUILD__CONTAINER_CODE_TAG, APPLICATION_ENV, APPLICATION_DEBUG


class FakeSentryScope:

    def set_tag(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def set_user(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def clear(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def __enter__(self) -> 'FakeSentryScope':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        pass


class FakeSentrySdk:
    def init(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def capture_exception(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def configure_scope(self) -> FakeSentryScope:
        return FakeSentryScope()


sentry = FakeSentrySdk()

if APPLICATION_SENTRY_DSN:
    import sentry_sdk
    sentry = sentry_sdk  # type: ignore

    if APPLICATION_SENTRY_ENABLED_FLASK:
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(APPLICATION_SENTRY_DSN, integrations=[FlaskIntegration()])
    else:
        sentry_sdk.init(APPLICATION_SENTRY_DSN)
    if DOCKER_BUILD__CONTAINER_CODE_COMMIT_HASH:
        sentry_sdk.set_tag('release', DOCKER_BUILD__CONTAINER_CODE_COMMIT_HASH)
    if DOCKER_BUILD__CONTAINER_SERVER_TIME:
        sentry_sdk.set_tag('docker_built_at', DOCKER_BUILD__CONTAINER_SERVER_TIME)
    if DOCKER_BUILD__CONTAINER_CODE_TAG:
        sentry_sdk.set_tag('docker_tag', DOCKER_BUILD__CONTAINER_CODE_TAG)
    sentry_sdk.set_tag('app_environment', APPLICATION_ENV)
    sentry_sdk.set_tag('app_debug', 'True' if APPLICATION_DEBUG else 'False')
