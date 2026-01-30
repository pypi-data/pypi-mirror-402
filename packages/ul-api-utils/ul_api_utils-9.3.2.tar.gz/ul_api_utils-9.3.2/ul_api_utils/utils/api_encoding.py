import gzip
from enum import Enum
from typing import Tuple, Optional

from ul_api_utils.const import ENCODING_MIME__GZIP


class ApiEncoding(Enum):
    NONE = 'NONE'
    GZIP = 'GZIP'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @property
    def mime(self) -> str:
        if self is ApiEncoding.NONE:
            return ''
        if self is ApiEncoding.GZIP:
            return ENCODING_MIME__GZIP
        raise NotImplementedError

    @staticmethod
    def accept_mimes(force: Optional['ApiEncoding'] = None) -> Tuple[str, ...]:
        if force is ApiEncoding.GZIP:
            return ENCODING_MIME__GZIP,  # noqa: C818
        if force is ApiEncoding.NONE:
            return tuple()
        return ENCODING_MIME__GZIP,  # noqa: C818

    @staticmethod
    def from_mime(mime: str) -> Optional['ApiEncoding']:
        if mime == ENCODING_MIME__GZIP:
            return ApiEncoding.GZIP
        if mime == '':
            return ApiEncoding.NONE
        return None

    def encode(self, data: bytes) -> bytes:
        if self is ApiEncoding.GZIP:
            return gzip.compress(data)
        if self is ApiEncoding.NONE:
            return data
        raise NotImplementedError

    def decode(self, data: bytes) -> bytes:
        if self is ApiEncoding.GZIP:
            return gzip.decompress(data)
        if self is ApiEncoding.NONE:
            return data
        raise NotImplementedError
