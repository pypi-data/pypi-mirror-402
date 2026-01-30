import decimal
from datetime import timedelta

import redis
import ormsgpack
import collections

from pydantic import ValidationError, BaseModel, TypeAdapter
from typing import Any, Type, overload, Iterator, KeysView, cast

from ul_api_utils.utils.instance_checks import isinstance_namedtuple
from ul_api_utils.utils.memory_db.errors import CompositeKeyError, UnsupportedParsingType

CompositeKeyT = tuple[str, Type[BaseModel]]
AnyKeyT = str | CompositeKeyT
AnyT = Any
RedisClientT = redis.StrictRedis | redis.Redis  # type: ignore
ExpiryT = int | timedelta | None


class BaseMemoryDbRepository(collections.abc.MutableMapping[str, AnyT]):
    def __init__(self, redis_client: RedisClientT) -> None:
        self._db = redis_client
        self._composite_key_max_length = 2

    @property
    def db(self) -> RedisClientT:
        return self._db

    def get(self, __key: str, *, parse_as_type: Type[BaseModel] | None = None, default: Any | None = None) -> AnyT | None:  # type: ignore
        try:
            if parse_as_type is None:
                return self[__key]
            return self[__key, parse_as_type]
        except KeyError:
            return default

    def set(self, __key: str, value: AnyT, *, expires: ExpiryT = None) -> None:
        packed_value = ormsgpack.packb(value, option=ormsgpack.OPT_SERIALIZE_PYDANTIC, default=self._default_serializer)
        self._db.set(__key, packed_value, ex=expires)

    @overload
    def __getitem__(self, key: str) -> AnyT:
        ...

    @overload
    def __getitem__(self, key: CompositeKeyT) -> AnyT:
        ...

    def __getitem__(self, key: AnyKeyT) -> AnyT:
        key_complex = isinstance(key, tuple)

        if not key_complex:
            single_key = cast(str, key)
            return ormsgpack.unpackb(self._db[single_key])

        composite_key = cast(CompositeKeyT, key)
        if len(composite_key) > self._composite_key_max_length:
            raise CompositeKeyError(f"Can't retrieve an item with {key=}. Composite key should have only two arguments.")

        composite_key_name, _parse_as_type = composite_key
        parsing_type_supported = issubclass(_parse_as_type, BaseModel) and _parse_as_type is not BaseModel
        if not parsing_type_supported:
            raise UnsupportedParsingType(f"Unsupported parsing type {_parse_as_type}.")
        value = ormsgpack.unpackb(self._db[composite_key_name])
        try:
            if isinstance(value, list):
                return TypeAdapter(list[_parse_as_type]).validate_python(value)  # type: ignore
            return TypeAdapter(_parse_as_type).validate_python(value)
        except ValidationError:
            raise UnsupportedParsingType(f"Could not parse the value of key '{composite_key_name}' with type {_parse_as_type}") from None

    def __setitem__(self, key: str, value: AnyT) -> None:
        self._db[key] = ormsgpack.packb(value, option=ormsgpack.OPT_SERIALIZE_PYDANTIC, default=self._default_serializer)

    def __delitem__(self, key: str) -> None:
        del self._db[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._db.keys())

    def keys(self) -> KeysView[str]:
        available_keys = [key.decode() for key in self._db.keys()]
        return cast(KeysView[str], available_keys)

    def clear(self) -> None:
        self._db.flushdb()

    @staticmethod
    def _default_serializer(obj: Any) -> Any:
        if isinstance_namedtuple(obj):
            return obj._asdict()
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, frozenset):
            return list(obj)
        raise TypeError
