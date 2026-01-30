import os

from ul_db_utils.modules.postgres_modules.db import DbConfig

from ul_api_utils.modules.api_sdk import ApiSdk
from ul_api_utils.modules.api_sdk_config import ApiSdkConfig, ApiSdkIdentifyTypeEnum, \
    ApiSdkFlaskDebuggingPluginsEnabled
from example.permissions import permissions
from ul_api_utils.resources.socketio import SocketIOConfigType, SocketIOConfig


sdk = ApiSdk(ApiSdkConfig(
    socket_config=SocketIOConfig(
        app_type=SocketIOConfigType.EXTERNAL_PROCESS,
        message_queue='redis://localhost:16379',
        logs_enabled=True,
        engineio_logs_enabled=False,
    ),
    service_name='example_service',
    permissions=permissions,
    cache_storage_uri='redis://localhost:16379',
    cache_default_ttl=60,
    rate_limit_storage_uri='redis://localhost:16379',
    rate_limit_identify=ApiSdkIdentifyTypeEnum.JWT_USER_ID,
    flask_debugging_plugins=ApiSdkFlaskDebuggingPluginsEnabled(
        flask_monitoring_dashboard=True,
    ),
    web_error_template='error.html.jinja2',
))


fake_models_dir = os.path.join(os.path.dirname(__file__), 'models')


db_config = DbConfig(uri='postgresql://admin:admin@localhost:45432/example', models_path=fake_models_dir)
