import json
from enum import Enum
from typing import Tuple, Any, Optional

import msgpack

from ul_api_utils.const import MIME__JSON, MIME__MSGPCK
from ul_api_utils.utils.json_encoder import CustomJSONEncoder


class ApiFormat(Enum):
    JSON = 'JSON'
    MESSAGE_PACK = 'MESSAGE_PACK'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def accept_mimes(force: Optional['ApiFormat'] = None) -> Tuple[str, ...]:
        if force is ApiFormat.MESSAGE_PACK:
            return MIME__MSGPCK,  # noqa: C818
        if force is ApiFormat.JSON:
            return MIME__JSON,  # noqa: C818
        return MIME__MSGPCK, MIME__JSON

    @property
    def mime(self) -> str:
        if self is ApiFormat.MESSAGE_PACK:
            return MIME__MSGPCK
        if self is ApiFormat.JSON:
            return MIME__JSON
        raise NotImplementedError

    @staticmethod
    def from_mime(mime: str) -> Optional['ApiFormat']:
        if mime == MIME__MSGPCK:
            return ApiFormat.MESSAGE_PACK
        if mime == MIME__JSON or (mime.startswith("application/") and mime.endswith("+json")):
            return ApiFormat.JSON
        return None

    def serialize_bytes(self, data: Any) -> bytes:
        if self is ApiFormat.MESSAGE_PACK:
            return msgpack.dumps(data, default=CustomJSONEncoder().default)
        if self is ApiFormat.JSON:
            return json.dumps(data, cls=CustomJSONEncoder).encode('utf-8')
        raise NotImplementedError

    def parse_bytes(self, data: bytes) -> Any:
        if self is ApiFormat.MESSAGE_PACK:
            return msgpack.unpackb(data, use_list=True)
        if self is ApiFormat.JSON:
            return json.loads(data)
        raise NotImplementedError

    def parse_text(self, data: str) -> Any:
        if self is ApiFormat.MESSAGE_PACK:
            return msgpack.unpackb(data.encode('utf-8'), use_list=True)
        if self is ApiFormat.JSON:
            return json.loads(data)
        raise NotImplementedError
