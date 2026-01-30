from typing import Dict, Union, Optional, Any, Iterable, Generic, TypeVar, Type, List

from pydantic import BaseModel

from ul_api_utils.api_resource.api_response import AnyJsonApiResponse
from ul_api_utils.api_resource.db_types import TDictable


class AnyJsonDbApiResponse(AnyJsonApiResponse):
    payload: Union[Optional[TDictable], Iterable[TDictable]]


TJsonObjApiResponsePayload = TypeVar('TJsonObjApiResponsePayload')


class JsonDbApiResponse(Generic[TJsonObjApiResponsePayload], AnyJsonApiResponse):

    @classmethod
    def _internal_use__mk_schema(cls, inner_type: Optional[Type[BaseModel]]) -> Type[BaseModel]:
        class _ResponseStd(BaseModel):
            ok: bool
            payload: inner_type  # type: ignore
            errors: List[Dict[str, Any]]
            total_count: Optional[int] = None
            count: Optional[int] = None
        return _ResponseStd
