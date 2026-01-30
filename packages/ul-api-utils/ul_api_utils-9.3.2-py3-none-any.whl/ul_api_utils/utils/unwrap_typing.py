from dataclasses import dataclass
from types import NoneType
from typing import NamedTuple, Type, Tuple, _GenericAlias, _UnionGenericAlias, Any, Union, Optional, TypeVar, Generic, Callable  # type: ignore

from ul_api_utils.api_resource.api_response import RootJsonApiResponsePayload


class TypingType(NamedTuple):
    value: Type[Any]

    def issubclassof(self, dest_type: Union[Type[Any], Tuple[Type[Any], ...]]) -> bool:
        try:
            if isinstance(dest_type, tuple):
                return any(issubclass(self.value, t) for t in dest_type)
            return issubclass(self.value, dest_type)
        except Exception:  # noqa: B902
            return False


class TypingGeneric(NamedTuple):
    origin: TypingType
    args: Tuple[TypingType, ...]


class TypingUnion(NamedTuple):
    args: Tuple[TypingType, ...]


class TypingOptional(NamedTuple):
    value: Union[TypingType, TypingUnion, TypingGeneric]


def unwrap_typing(t: Type[Any]) -> Union[TypingGeneric, TypingUnion, TypingType, TypingOptional]:
    tt = type(t)
    if tt == _GenericAlias:
        return TypingGeneric(origin=unwrap_typing(t.__origin__), args=tuple(unwrap_typing(it) for it in t.__args__))  # type: ignore
    if tt == _UnionGenericAlias:
        if t.__origin__ == Union:
            if len(t.__args__) == 2:
                if t.__args__[0] == NoneType:
                    return TypingOptional(value=unwrap_typing(t.__args__[1]))  # type: ignore
                if t.__args__[1] == NoneType:
                    return TypingOptional(value=unwrap_typing(t.__args__[0]))  # type: ignore

            return TypingUnion(args=tuple(unwrap_typing(it) for it in t.__args__))  # type: ignore
        raise NotImplementedError()
    return TypingType(t)


T = TypeVar('T')
TVal = TypeVar('TVal')
TValRoot = TypeVar('TValRoot', bound=RootJsonApiResponsePayload[Any])


def default_constructor(value_type: Type[TVal], data: Any) -> TVal:
    return value_type(data)  # type: ignore


@dataclass
class UnwrappedOptionalObjOrListOfObj(Generic[TVal]):
    many: bool
    optional: bool
    value_type: Type[TVal]

    def apply(self, payload: Any, constructor: Optional[Callable[[Type[T], Any], T]] = default_constructor) -> Optional[TVal]:
        if payload is None:
            assert self.optional, 'payload must not be None'
            return None
        if self.many:
            try:
                it = iter(payload)
            except Exception:  # noqa: B902
                raise AssertionError('payload is not iterable')
            return [constructor(self.value_type, i) for i in it]  # type: ignore
        return constructor(self.value_type, payload)  # type: ignore

    @staticmethod
    def parse(t: Type[Any], type_constraint: Optional[Type[TVal | TValRoot]]) -> 'Optional[UnwrappedOptionalObjOrListOfObj[TVal]]':
        unwrapped_t = unwrap_typing(t)

        many = False
        optional = False
        value_type: TypingType

        if isinstance(unwrapped_t, TypingType):
            value_type = unwrapped_t
        elif isinstance(unwrapped_t, TypingGeneric) and len(unwrapped_t.args) == 1:
            if unwrapped_t.origin.value != list:  # noqa: E721
                return None
            if not isinstance(unwrapped_t.args[0], TypingType):
                return None  # type: ignore
            value_type = unwrapped_t.args[0]
            many = True
        elif isinstance(unwrapped_t, TypingOptional):
            optional = True
            if isinstance(unwrapped_t.value, TypingGeneric):
                if unwrapped_t.value.origin.value != list:  # noqa: E721
                    return None
                if len(unwrapped_t.value.args) != 1 or not isinstance(unwrapped_t.value.args[0], TypingType):
                    return None
                value_type = unwrapped_t.value.args[0]
                many = True
            elif isinstance(unwrapped_t.value, TypingType):
                value_type = unwrapped_t.value
            else:
                return None
        else:
            return None

        if not isinstance(value_type, TypingType):
            return None  # type: ignore

        if type_constraint is not None:
            if not value_type.issubclassof(type_constraint):
                return None

        return UnwrappedOptionalObjOrListOfObj(many, optional, value_type.value)
