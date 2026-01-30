import functools
from typing import Callable, TypeVar, Any

from flask import g

TFn = TypeVar("TFn", bound=Callable[..., Any])


DEFAULT_OBJ = object()


def cached_per_request(key: str) -> Callable[[TFn], TFn]:
    def wrapper(fn: Callable[[...], Any]) -> Any:  # type: ignore
        @functools.wraps(fn)
        def wr(*args: Any, **kwargs: Any) -> Any:
            cached_res = getattr(g, key, DEFAULT_OBJ)
            if cached_res is not DEFAULT_OBJ:
                return cached_res
            res = fn(*args, **kwargs)
            setattr(g, key, res)
            return res
        return wr
    return wrapper
