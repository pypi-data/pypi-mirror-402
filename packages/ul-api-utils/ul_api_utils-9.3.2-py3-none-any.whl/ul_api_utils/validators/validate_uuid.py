from typing import Any
from uuid import UUID

from ul_api_utils.errors import SimpleValidateApiError


def validate_uuid4(uuid: Any) -> None:
    try:
        UUID(uuid, version=4)
    except ValueError:
        raise SimpleValidateApiError('invalid uuid')
