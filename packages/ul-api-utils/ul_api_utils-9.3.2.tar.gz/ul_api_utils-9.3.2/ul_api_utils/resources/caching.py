import functools
import hashlib
import inspect
import itertools
import logging
from _hashlib import HASH
from collections import defaultdict
from enum import Enum
from typing import Optional, Callable, Dict, Tuple, List, Union, Literal, cast, TypeVar, Any, Set, TypedDict

import ormsgpack
from pydantic import ValidationError
from werkzeug import Response as BaseResponse

from flask import request
from flask_caching import Cache, CachedResponse

from ul_api_utils.api_resource.api_response import ApiResponse, JsonApiResponse
from ul_api_utils.conf import APPLICATION_DEBUG
from ul_api_utils.utils.constants import TKwargs
from ul_api_utils.utils.json_encoder import CustomJSONEncoder

TCacheModeStr = Union[Literal['READ'], Literal['REFRESH']]
TFn = TypeVar("TFn", bound=Callable[..., ApiResponse])


class ULCacheMode(Enum):
    READ = 'READ'
    REFRESH = 'REFRESH'

    @staticmethod
    def compile_mode(mode: Union[TCacheModeStr, 'ULCacheMode']) -> str:
        if isinstance(mode, ULCacheMode):
            return mode.value
        assert isinstance(mode, str)
        m = mode.strip().upper()
        return ULCacheMode(m).value


TCacheMode = Union[TCacheModeStr, 'ULCacheMode']


class ULCacheConfig(TypedDict):     # https://flask-caching.readthedocs.io/en/latest/#configuring-flask-caching
    CACHE_TYPE: str
    CACHE_REDIS_HOST: str
    CACHE_REDIS_PORT: str
    CACHE_REDIS_PASSWORD: str
    CACHE_KEY_PREFIX: str
    CACHE_DEFAULT_TIMEOUT: int
    CACHE_SOURCE_CHECK: bool


class ULCache(Cache):

    @property
    def tags_map(self) -> Dict[Tuple[str, ...], Set[str]]:
        if self.cache.has(':tags_map'):
            return self.cache.get(':tags_map')
        else:
            return defaultdict(set)

    @tags_map.setter
    def tags_map(self, value: Dict[Tuple[str], Set[str]]) -> None:
        self.cache.set(':tags_map', value, -1)

    @staticmethod
    def _has_common_elements(seq: Set[Tuple[str, ...]]) -> bool:
        return bool(functools.reduce(set.intersection, map(set, seq)))

    @staticmethod
    def _format_cache_key(parts: List[Any]) -> str:
        return ':' + ':'.join([p for p in parts if p])

    def make_cache_key(
        self,
        fn: TFn,
        source_check: bool,
        hash_method: Callable[[bytes], HASH],
    ) -> str:
        cache_key_parts: List[str] = [request.path]
        cache_hash: HASH | None = None
        if request.args:
            args_as_sorted_tuple = tuple(sorted(pair for pair in request.args.items(multi=True)))

            args_as_bytes = str(args_as_sorted_tuple).encode()
            cache_hash = hash_method(args_as_bytes)

        # Use the source code if source_check is True and update the
        # cache_hash before generating the hashing and using it in cache_key
        if source_check and callable(fn):
            func_source_code = inspect.getsource(fn)
            if cache_hash is not None:
                cache_hash.update(func_source_code.encode("utf-8"))
            else:
                cache_hash = hash_method(func_source_code.encode("utf-8"))
        cache_hash_str = str(cache_hash.hexdigest()) if cache_hash is not None else ''
        cache_key_parts.append(cache_hash_str)

        return self._format_cache_key(cache_key_parts)

    def cache_refresh_wrap(
        self,
        tags: Tuple[str, ...] | str,
    ) -> Callable[[TFn], TFn]:
        def wrap(fn: TFn) -> TFn:
            assert fn.__module__, 'empty __module__ of function'
            func_tags = tags if isinstance(tags, tuple) else (tags,)

            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: TKwargs) -> Tuple[BaseResponse, int]:
                dependent_keys = []
                tags_map = self.tags_map.copy()

                for t in tags_map.keys():
                    stored_tags = t if isinstance(t, tuple) else (t,)
                    if self._has_common_elements({stored_tags, func_tags}):
                        dependent_keys.append(tags_map[stored_tags].copy())
                        tags_map[stored_tags] = set()
                cache_list_to_reset: List[str] = list(itertools.chain.from_iterable(dependent_keys))
                self.delete_many(*cache_list_to_reset)
                tags_map[func_tags] = set()
                self.tags_map = tags_map
                return self._call_fn(fn, *args, **kwargs)

            return cast(TFn, wrapper)
        return wrap

    def cache_noop(
        self,
    ) -> Callable[[TFn], TFn]:
        def wrap(fn: TFn) -> TFn:
            assert fn.__module__, 'empty __module__ of function'
            return fn

        return wrap

    def cache_read_wrap(
        self,
        tags: Tuple[str, ...] | str,
        timeout: Optional[int] = None,
        source_check: Optional[bool] = None,
        hash_method: Callable[[bytes], HASH] = hashlib.md5,
    ) -> Callable[[TFn], TFn]:
        def cache_wrap(fn: TFn) -> TFn:
            assert fn.__module__, 'empty __module__ of function'

            nonlocal source_check
            if source_check is None:
                source_check = self.source_check or False

            func_tags = tags if isinstance(tags, tuple) else (tags,)
            if self.tags_map.get(func_tags) is None:
                self.tags_map[func_tags] = set()

            logger = logging.getLogger(fn.__module__)

            @functools.wraps(fn)
            def cache_wrapper(*args: Any, **kwargs: TKwargs) -> Tuple[BaseResponse | CachedResponse, int]:
                try:
                    assert source_check is not None  # just for mypy
                    cache_key = self.make_cache_key(fn, source_check, hash_method)
                    if resp := self.cache.get(cache_key):
                        try:
                            resp = JsonApiResponse(**ormsgpack.unpackb(resp))
                        except ValidationError:
                            logger.error(f'cache read error of {fn.__name__} :: response not type of {JsonApiResponse.__name__}')
                            raise

                    found = True
                    # If the value returned by cache.get() is None
                    # it might be because the key is not found in the cache
                    # or because the cached value is actually None
                    if resp is None:
                        found = self.cache.has(cache_key)
                except Exception as e:  # noqa: B902 # cuz lot of variations of cache factory impementaions
                    logger.error(f'error due cache check :: {e}')
                    return self._call_fn(fn, *args, **kwargs)
                if not found:
                    tags_map = self.tags_map.copy()
                    tags_map[func_tags].add(cache_key)
                    resp = self._call_fn(fn, *args, **kwargs)
                    try:
                        self.cache.set(
                            key=cache_key,
                            value=ormsgpack.packb(resp, default=CustomJSONEncoder().default),
                            timeout=timeout,
                        )
                    except Exception as e:  # noqa: B902 # cuz lot of variations of cache factory impementaions
                        if APPLICATION_DEBUG:
                            raise
                        logger.error(f'exception possibly due to cache response :: {e}')
                    self.tags_map = self.tags_map | tags_map
                return resp

            return cast(TFn, cache_wrapper)
        return cache_wrap
