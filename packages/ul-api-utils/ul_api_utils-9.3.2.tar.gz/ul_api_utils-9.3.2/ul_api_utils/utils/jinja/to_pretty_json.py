import json
from typing import Any


def to_pretty_json(value: Any) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:  # noqa: B902
            return value
    return json.dumps(value, sort_keys=True, indent=4, separators=(',', ': '))
