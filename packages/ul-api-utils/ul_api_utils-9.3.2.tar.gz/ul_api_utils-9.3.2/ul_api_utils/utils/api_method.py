from enum import Enum, unique
from typing import Union, List, Tuple, Any, Literal

from ul_api_utils.const import REQUEST_METHOD__PUT, REQUEST_METHOD__GET, REQUEST_METHOD__POST, \
    REQUEST_METHOD__PATCH, REQUEST_METHOD__DELETE, REQUEST_METHOD__OPTIONS, REQUEST_METHOD__QUERY

TMethodStr = Union[Literal['GET'], Literal['POST'], Literal['PUT'], Literal['PATCH'], Literal['DELETE'], Literal['OPTIONS']]
TMethod = Union[TMethodStr, 'ApiMethod', List[TMethodStr], Tuple[TMethodStr, ...], List['ApiMethod'], Tuple['ApiMethod', ...]]
TMethodShort = Union[TMethodStr, 'ApiMethod']


@unique
class ApiMethod(Enum):
    PUT = REQUEST_METHOD__PUT
    GET = REQUEST_METHOD__GET
    POST = REQUEST_METHOD__POST
    QUERY = REQUEST_METHOD__QUERY
    PATCH = REQUEST_METHOD__PATCH
    DELETE = REQUEST_METHOD__DELETE
    OPTIONS = REQUEST_METHOD__OPTIONS

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            try:
                other = type(self)(other.upper())
            except Exception:  # noqa: B902
                return False
        return super(ApiMethod, self).__eq__(other)

    @staticmethod
    def compile_methods(methods: TMethod) -> Tuple[List[str], List['ApiMethod']]:
        str_res_methods = []
        enum_res_methods = []
        for m in (list(methods) if isinstance(methods, (list, tuple)) else [methods]):
            if isinstance(m, ApiMethod):
                str_res_methods.append(m.value)
                enum_res_methods.append(m)
            else:
                assert isinstance(m, str)
                m = m.strip().upper()  # type: ignore
                enum_res_methods.append(ApiMethod(m))
                str_res_methods.append(m)
        return str_res_methods, enum_res_methods


NO_REQUEST_BODY_METHODS = {ApiMethod.GET, ApiMethod.OPTIONS}
