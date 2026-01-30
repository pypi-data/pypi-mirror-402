import contextlib
from typing import Generator, Any, TYPE_CHECKING
from uuid import UUID

from flask import g

from ul_api_utils.errors import NotCheckedResponseInternalApiError

if TYPE_CHECKING:
    from ul_api_utils.internal_api.internal_api_response import InternalApiResponse


@contextlib.contextmanager
def internal_api_check_context() -> Generator[None, None, None]:
    g._api_utils_internal_api_context = []  # type: ignore

    try:
        yield

        invalid_resp = []
        for resp in g._api_utils_internal_api_context:  # type: ignore
            if not resp._internal_use__checked_once:
                invalid_resp.append(resp)

        if len(invalid_resp) > 0:
            info = ", ".join(f"\"{r._internal_use__info}\"" for r in invalid_resp)
            raise NotCheckedResponseInternalApiError(
                f'internal api responses must be checked once at least :: [{info}]',
            )
    finally:
        g._api_utils_internal_api_context.clear()  # type: ignore


def internal_api_check_context_add_response(resp: 'InternalApiResponse[Any]') -> None:
    if hasattr(g, '_api_utils_internal_api_context'):
        g._api_utils_internal_api_context.append(resp)  # type: ignore


def internal_api_check_context_rm_response(id: UUID) -> None:
    if hasattr(g, '_api_utils_internal_api_context'):
        prev = g._api_utils_internal_api_context  # type: ignore
        g._api_utils_internal_api_context = [r for r in prev if r.id != id]  # type: ignore
