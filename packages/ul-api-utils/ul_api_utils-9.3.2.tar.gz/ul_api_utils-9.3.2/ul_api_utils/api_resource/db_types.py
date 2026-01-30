from typing import Union, Dict, Any, Tuple, Optional, Iterable

from pydantic import BaseModel
from ul_db_utils.model.base_model import BaseModel as DbBaseModel
from flask_sqlalchemy.model import Model

# TODO: remove DbBaseModel/Model from it BECAUSE IT loads sqlalchemy (>20mb of code)
TDictable = Union[Dict[str, Any], BaseModel, Tuple[Any, ...], DbBaseModel, Model]
TPayloadInputUnion = Union[Optional[TDictable], Iterable[TDictable]]
