from typing import Any, Dict, Optional, Union, Type, TypeVar, Tuple, TYPE_CHECKING, get_origin, get_args
from typing import _GenericAlias  # type: ignore

from pydantic import BaseModel, RootModel

from ul_api_utils.utils.json_encoder import to_dict

if TYPE_CHECKING:
    from ul_api_utils.api_resource.db_types import TDictable

TPydanticModel = TypeVar('TPydanticModel', bound=BaseModel)


def set_model(model: Type[TPydanticModel], data: Union[Dict[str, Any], TPydanticModel]) -> TPydanticModel:
    if isinstance(data, model):
        return data
    if issubclass(model, RootModel):
        return model(data).root
    assert isinstance(data, dict), f'data must be dict. "{type(data).__name__}" was given'
    return model(**data)


def set_model_dictable(model: Type[TPydanticModel], data: 'TDictable') -> Optional[TPydanticModel]:
    if isinstance(data, model):
        return data
    res: Optional[Dict[str, Any]] = to_dict(data)
    if res is None:
        return None
    if issubclass(model, RootModel):
        return model(data).root
    return model(**res)


def get_typing(t: Type[Any]) -> Tuple[Type[Any], ...]:
    if type(t) == _GenericAlias:  # noqa: E721
        return get_origin(t), *(it for it in get_args(t))
    if t.__class__.__name__ == 'ModelMetaclass':
        if hasattr(t, '_generic_params') and t._generic_params is not None:
            unspecialized_class = t.__bases__[0]
            return unspecialized_class, t._generic_params[0]
    return t,  # noqa: C818
