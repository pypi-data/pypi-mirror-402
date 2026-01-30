import logging
import os
import sys
from datetime import datetime
from typing import Optional

from ul_py_tool.utils.colors import NC, FG_BLUE

from ul_api_utils.const import APPLICATION_ENV__LOCAL, API_PATH__SWAGGER, API_PATH__SWAGGER_SPEC
from ul_api_utils.utils.decode_base64 import decode_base64_to_string
from ul_api_utils.utils.flags import Flagged

APPLICATION_START_DT = datetime.fromisoformat(os.environ.get('APPLICATION_START_DT', datetime.now().isoformat()))
APPLICATION_DEBUGGER_PIN = os.environ.get('APPLICATION_DEBUGGER_PIN', '1232344321')
assert len(APPLICATION_DEBUGGER_PIN) > 0
APPLICATION_GUNICORN_WORKERS = os.environ.get('APPLICATION_GUNICORN_WORKERS', '')
DOCKER_BUILD__CONTAINER_CODE_COMMIT_HASH = os.environ.get('DOCKER_BUILD__CONTAINER_CODE_COMMIT_HASH', '')
DOCKER_BUILD__CONTAINER_SERVER_TIME = os.environ.get('DOCKER_BUILD__CONTAINER_SERVER_TIME', '')
DOCKER_BUILD__CONTAINER_CODE_TAG = os.environ.get('DOCKER_BUILD__CONTAINER_CODE_TAG', '')

APPLICATION_ENV: str = os.environ.get('APPLICATION_ENV', APPLICATION_ENV__LOCAL)  # TODO: make it required!
APPLICATION_ENV_IS_LOCAL = APPLICATION_ENV == APPLICATION_ENV__LOCAL

APPLICATION_DIR: str = os.path.abspath(os.environ.get('APPLICATION_DIR', os.getcwd()))
APPLICATION_TMP: str = os.path.join(APPLICATION_DIR, '.tmp')

APPLICATION_UNDER_DOCKER = '/docker_app/' in os.getcwd()

APPLICATION_DEBUG = os.environ.get('APPLICATION_DEBUG', '0') == '1'  # this env var set in app-utils
APPLICATION_DEBUG_LOGGING = os.environ.get('APPLICATION_DEBUG_LOGGING', '0') == '1'  # this env var set in app-utils

_APPLICATION_JWT_PUBLIC_KEY = os.environ.get('APPLICATION_JWT_PUBLIC_KEY', None) or None  # "or None" in case empty string. TODO: make it required!
APPLICATION_JWT_PUBLIC_KEY: str = decode_base64_to_string(_APPLICATION_JWT_PUBLIC_KEY) if _APPLICATION_JWT_PUBLIC_KEY is not None else ''

_APPLICATION_JWT_PRIVATE_KEY = os.environ.get('APPLICATION_JWT_PRIVATE_KEY', None) or None  # "or None" in case empty string
APPLICATION_JWT_PRIVATE_KEY: Optional[str] = decode_base64_to_string(_APPLICATION_JWT_PRIVATE_KEY) if _APPLICATION_JWT_PRIVATE_KEY is not None else None

APPLICATION_LOG_FORMAT = os.environ.get(
    'APPLICATION_LOG_FORMAT',
    f'%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s |'
    f'{FG_BLUE if APPLICATION_ENV_IS_LOCAL and APPLICATION_DEBUG else ""} %(message)s{NC if APPLICATION_ENV_IS_LOCAL and APPLICATION_DEBUG else ""}',
)
assert len(APPLICATION_LOG_FORMAT) and '(message)' in APPLICATION_LOG_FORMAT

os.makedirs(APPLICATION_TMP, exist_ok=True)

APPLICATION_LOG_LEVEL = os.environ.get('APPLICATION_LOG_LEVEL', os.environ.get('LOGLEVEL', 'INFO')).strip().upper()
_LOG_MAP = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
}
assert APPLICATION_LOG_LEVEL in _LOG_MAP

APPLICATION_SENTRY_DSN = os.environ.get('APPLICATION_SENTRY_DSN', '')
APPLICATION_SENTRY_ENABLED_FLASK = os.environ.get('APPLICATION_SENTRY_FLASK', '1') == '1'

APPLICATION_F = Flagged(os.environ.get('APPLICATION_F', ''))

APPLICATION_SWAGGER_SPECIFICATION_PATH = os.environ.get('APPLICATION_SWAGGER_SPECIFICATION_PATH', API_PATH__SWAGGER_SPEC)
APPLICATION_SWAGGER_PATH = os.environ.get('APPLICATION_SWAGGER_PATH', API_PATH__SWAGGER)

logging.basicConfig(
    handlers=[logging.StreamHandler(sys.stdout)],
    level=_LOG_MAP[APPLICATION_LOG_LEVEL],
    format=APPLICATION_LOG_FORMAT,
)

logging.getLogger('').setLevel(_LOG_MAP[APPLICATION_LOG_LEVEL])
