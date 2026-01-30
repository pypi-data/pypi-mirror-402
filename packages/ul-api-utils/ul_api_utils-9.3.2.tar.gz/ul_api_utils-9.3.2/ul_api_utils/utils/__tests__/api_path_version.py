from ul_api_utils.utils.api_path_version import ApiPathVersion


def test_path_compilation() -> None:
    assert ApiPathVersion.NO_VERSION.compile_path('some') == '/some'
    assert ApiPathVersion.NO_VERSION.compile_path('some', 'additional') == '/additional/some'
    assert ApiPathVersion.NO_VERSION.compile_path('some', 'additional', q={"a": 123}) == '/additional/some?a=123'

    assert ApiPathVersion.V01.compile_path('some', 'additional') == '/additional/v1/some'
    assert ApiPathVersion.V01.compile_path('some', 'additional', q={"a": 123}) == '/additional/v1/some?a=123'

    assert ApiPathVersion.NO_PREFIX.compile_path('some', 'additional') == '/some'
    assert ApiPathVersion.NO_PREFIX.compile_path('some', 'additional', q={"a": 123}) == '/some?a=123'

    assert ApiPathVersion.NO_VERSION.compile_path('') == ''
    assert ApiPathVersion.NO_VERSION.compile_path('', '/api') == '/api'
