from typing import Any, Dict, TypeVar, Tuple, Union

from flask import Response

TKwargs = TypeVar('TKwargs', bound=Dict[str, Any])
TJsonResponse = Union[Tuple[str, int], Tuple[Response, int]]
TJsonObj = Dict[str, Any]
