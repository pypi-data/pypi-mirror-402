from typing import Optional, Any, Dict, List, Tuple, Union

from pydantic import ConfigDict, BaseModel


class InternalApiResponseErrorObj(BaseModel):
    error_type: str
    error_message: str
    error_location: Optional[Union[List[str], str, Tuple[str, ...]]] = None
    error_kind: Optional[str] = None
    error_input: Optional[Any] = None
    other: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
