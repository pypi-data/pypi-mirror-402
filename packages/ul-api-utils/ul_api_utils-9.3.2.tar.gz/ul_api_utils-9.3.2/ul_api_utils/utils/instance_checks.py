from typing import Any


def isinstance_namedtuple(obj: Any) -> bool:
    namedtuple_unique_attributes = ('_asdict', '_fields')
    is_tuple = isinstance(obj, tuple)
    has_namedtuple_attributes = hasattr(obj, namedtuple_unique_attributes[0]) and hasattr(obj, namedtuple_unique_attributes[1])
    return has_namedtuple_attributes and is_tuple


def is_iterable(obj: Any) -> bool:
    try:
        iter(obj)
    except TypeError:
        return False
    return True
