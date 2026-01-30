from enum import Enum
from typing import Optional, Mapping, Union, Dict, Any


class ApiPathVersion(Enum):
    V01 = 'v1'
    V02 = 'v2'
    V03 = 'v3'
    V04 = 'v4'
    V05 = 'v5'
    V06 = 'v6'
    V07 = 'v7'
    V08 = 'v8'
    V09 = 'v9'
    V10 = 'v10'

    NO_VERSION = "no-version"
    NO_PREFIX = 'no-prefix'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'

    @staticmethod
    def cleanup_q(q: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if q is None:
            return None
        res = {}
        for k, v in q.items():
            if v is not None:
                res[k] = v
        return res

    def compile_path(self, path: str, prefix: str = "", *, q: Optional[Mapping[str, Union[int, str]]] = None) -> str:
        assert '?' not in path, f'restricted symbol "?" was found in url.path="{path}"'
        assert '&' not in path, f'restricted symbol "&" was found in url.path="{path}"'
        assert '?' not in prefix, f'restricted symbol "?" was found in url.prefix="{prefix}"'
        assert '&' not in prefix, f'restricted symbol "&" was found in url.prefix="{prefix}"'

        qr = ''
        if q:
            for k, kv in q.items():
                if kv is None:
                    continue  # type: ignore
                qr += ('?' if len(qr) == 0 else '&') + f'{k}={kv}'

        if self is ApiPathVersion.NO_PREFIX:
            if not path:
                return qr
            return f'/{path.lstrip("/")}{qr}'

        if self is ApiPathVersion.NO_VERSION:
            if not path:
                return f'{"/" if prefix else ""}{prefix.lstrip("/")}{qr}'
            return f'{"/" if prefix else ""}{prefix.strip("/")}/{path.lstrip("/")}{qr}'

        assert prefix, f'prefix must not be empty. {prefix} was given'

        if not path:
            return f'/{prefix.strip("/")}/{self.value}{qr}'
        return f'/{prefix.strip("/")}/{self.value}/{path.lstrip("/")}{qr}'
