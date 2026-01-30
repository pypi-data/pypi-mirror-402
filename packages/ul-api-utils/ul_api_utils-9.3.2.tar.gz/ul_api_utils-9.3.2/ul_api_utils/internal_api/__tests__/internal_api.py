from ul_api_utils.internal_api.internal_api import InternalApi
from ul_api_utils.internal_api.internal_api_response import InternalApiResponseCheckLevel
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.api_path_version import ApiPathVersion


def test_internal_api() -> None:
    ia = InternalApi('http://someurl.com')

    assert ia._path_prefix == '/api'
    assert ia._entry_point == 'http://someurl.com'

    ia = InternalApi('http://someurl.com/with-prefix/some')
    assert ia._path_prefix == '/with-prefix/some'
    assert ia._entry_point == 'http://someurl.com'

    ia = InternalApi('http://someurl.com/', path_prefix='')
    assert ia._path_prefix == ''
    assert ia._entry_point == 'http://someurl.com'


def test_internal_api_google() -> None:
    ia = InternalApi('https://google.com')

    ia.test_override(ApiMethod.GET, '/search', 200, response_json={"value": "123123"}, v=ApiPathVersion.NO_PREFIX)

    resp = ia.request_get('/search', v=ApiPathVersion.NO_PREFIX).check(level=InternalApiResponseCheckLevel.STATUS_CODE)

    assert resp.payload_raw == {"value": "123123"}
