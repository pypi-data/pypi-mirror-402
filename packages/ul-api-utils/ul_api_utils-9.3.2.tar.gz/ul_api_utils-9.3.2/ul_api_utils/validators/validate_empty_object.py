from typing import Any

from ul_api_utils.errors import SimpleValidateApiError


def validate_empty_object(obj_id: str, model: Any) -> Any:
    obj = model.query.filter_by(id=obj_id).first()
    if not obj:
        raise SimpleValidateApiError(f'{model.__name__} data was not found')
    return obj
