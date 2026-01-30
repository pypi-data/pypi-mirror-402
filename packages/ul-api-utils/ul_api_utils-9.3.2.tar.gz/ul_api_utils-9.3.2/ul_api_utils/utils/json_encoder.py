import dataclasses
import decimal
import json
from base64 import b64encode
from datetime import date, datetime, time
from enum import Enum
from json import JSONEncoder
from typing import Dict, Any, Union, List, Optional, TYPE_CHECKING
from uuid import UUID

from flask.json.provider import DefaultJSONProvider
from frozendict import frozendict
from pydantic import BaseModel

from flask_sqlalchemy.query import Query
from flask_sqlalchemy.model import Model, DefaultMeta

from sqlalchemy.orm import Query, registry

from ul_db_utils.modules.postgres_modules.db import DbModel
from ul_db_utils.model.base_model import BaseModel as DbBaseModel
from ul_api_utils.utils.imports import has_already_imported_db

if TYPE_CHECKING:
    from ul_api_utils.api_resource.api_response_db import TDictable


def to_dict(obj: 'TDictable') -> Optional[Dict[str, Any]]:
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, tuple) and hasattr(obj, '_asdict'):  # NamedTuple
        return obj._asdict()
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if has_already_imported_db():
        if isinstance(obj, DbBaseModel) or isinstance(obj, DbModel):
            return obj.to_dict()
        if isinstance(obj, Model):
            fields = {}
            for field in (x for x in dir(obj) if not x.startswith('_') and x != 'metadata'):
                val = obj.__getattribute__(field)
                # is this field method defination, or an SQLalchemy object
                if not hasattr(val, "__call__") and not isinstance(val, Query):  # noqa: B004
                    if isinstance(val, datetime):
                        val = str(val.isoformat())
                    if isinstance(val, UUID):
                        val = str(val)
                    if isinstance(val, bytes):
                        val = b64encode(val).decode()
                    if isinstance(val, registry):
                        continue
                    fields[field] = val
            return fields
    return None


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj: object) -> Union[str, Dict[str, Any], List[Any], None]:
        if isinstance(obj, (decimal.Decimal)):
            return str(obj)
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if isinstance(obj, datetime):
            return str(obj.isoformat())
        if isinstance(obj, date):
            return str(obj.isoformat())
        if isinstance(obj, time):
            return str(obj.isoformat())
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return str(obj.value)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, frozendict):
            return dict(obj)
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)  # type: ignore
        if hasattr(obj, "__html__"):  # it needs for Flask ?
            return str(obj.__html__())

        if has_already_imported_db():
            if isinstance(obj, DbBaseModel):
                return obj.to_dict()
            if isinstance(obj, Query) or isinstance(obj, DefaultMeta):
                return None
            if isinstance(obj, Model):
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    val = obj.__getattribute__(field)
                    # is this field method defination, or an SQLalchemy object
                    if not hasattr(val, "__call__") and not isinstance(val, Query):  # noqa: B004
                        if isinstance(val, datetime):
                            val = str(val.isoformat())
                        if isinstance(val, UUID):
                            val = str(val)
                        if isinstance(val, bytes):
                            val = b64encode(val).decode()
                        if isinstance(val, registry):
                            continue
                        fields[field] = val
                return fields
        return super().default(obj)


class SocketIOJsonWrapper:
    @staticmethod
    def dumps(*args: Any, **kwargs: Any) -> str:
        if 'cls' not in kwargs:
            kwargs['cls'] = CustomJSONEncoder
        return json.dumps(*args, **kwargs)

    @staticmethod
    def loads(*args: Any, **kwargs: Any) -> Any:
        return json.loads(*args, **kwargs)


class CustomJSONProvider(DefaultJSONProvider):
    def __init__(self, app):
        super().__init__(app)
        self.encoder = CustomJSONEncoder()

    def default(self, obj) -> Union[str, Dict[str, Any], List[Any], None]:
        return self.encoder.default(obj)
