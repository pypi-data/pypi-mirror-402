import os.path
from typing import Union, Dict, Any, List

THIS_LIB_CWD = os.path.dirname(__file__)

PY_FILE_SUF = '.py'

RESPONSE_PROP_OK = 'ok'
RESPONSE_PROP_STATUS = 'status'
RESPONSE_PROP_PAYLOAD = 'payload'
RESPONSE_PROP_COUNT = 'count'
RESPONSE_PROP_TOTAL = 'total_count'
RESPONSE_PROP_ERRORS = 'errors'
RESPONSE_PROP_DEBUG_STATS = '_debug_stats_'


APPLICATION_ENV__LOCAL = 'local'
APPLICATION_ENV__DEV = 'dev'
APPLICATION_ENV__QA = 'qa'
APPLICATION_ENV__STAGING = 'staging'
APPLICATION_ENV__PROD = 'prod'


RESPONSE_HEADER__CONTENT_TYPE = 'Content-Type'
RESPONSE_HEADER__AUTHORIZATION = 'Authorization'
RESPONSE_HEADER__WWW_AUTH = 'WWW-Authenticate'
REQUEST_HEADER__CONTENT_TYPE = 'Content-Type'
REQUEST_HEADER__CONTENT_ENCODING = 'Content-Encoding'
REQUEST_HEADER__ACCEPT_CONTENT_ENCODING = 'Accept-Encoding'
REQUEST_HEADER__DEBUGGER = 'x-api-utils-debugger-pin'
REQUEST_HEADER__INTERNAL = 'x-api-utils-internal-api'
REQUEST_HEADER__ACCEPT = 'Accept'
REQUEST_HEADER__X_FORWARDED_FOR = 'X-Forwarded-For'
REQUEST_HEADER__USER_AGENT = 'User-Agent'


MIME__AVRO = 'application/avro'
MIME__JSON = 'application/json'
MIME__MSGPCK = 'application/x-msgpack'


ENCODING_MIME__GZIP = 'gzip'

REQUEST_METHOD__PUT = 'PUT'
REQUEST_METHOD__GET = 'GET'
REQUEST_METHOD__POST = 'POST'
REQUEST_METHOD__QUERY = 'QUERY'
REQUEST_METHOD__PATCH = 'PATCH'
REQUEST_METHOD__DELETE = 'DELETE'
REQUEST_METHOD__OPTIONS = 'OPTIONS'


UNDEFINED = 'UNDEFINED'
OOPS = '...Ooops something went wrong. internal error'


TRestJson = Union[List[Dict[str, Any]], Dict[str, Any]]


API_PATH__SWAGGER = '/swagger'
API_PATH__SWAGGER_SPEC = '/swagger-specification'
API_PATH__PERMISSIONS = '/permissions'
API_PATH__DEBUGGER_JS_UI = '/ul-debugger-ui.js'
API_PATH__DEBUGGER_JS_MAIN = '/ul-debugger-main.js'


INTERNAL_API__DEFAULT_PATH_PREFIX = '/api'

AUTO_GZIP_THRESHOLD_LENGTH = 1000

CRON_EXPRESSION_VALIDATION_REGEX = "(^((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))" \
                                   "((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)\s+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)" \
                                   "([1-9]|[12][0-9]|3[01]))*|\*)\s+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)" \
                                   "([1-9]|1[0-2]))*|\*|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|des))\s+((\*\/)?[0-6]" \
                                   "((\,|\-|\/)[0-6])*|\*|00|(sun|mon|tue|wed|thu|fri|sat))\s*$)|@(annually|yearly|monthly|weekly|daily|hourly|reboot)"  # noqa

MAX_UTC_OFFSET_SECONDS = 50400
MIN_UTC_OFFSET_SECONDS = -43200
