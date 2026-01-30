from typing import Any, List, Dict

from flask import url_for


# template url_for
def t_url_for(*args: Any, **kwargs: Any) -> str:
    res_args: List[Any] = []
    res_kwargs: Dict[str, Any] = {}

    for arg in args:
        if isinstance(arg, dict):
            res_kwargs.update(arg)
        elif isinstance(arg, (list, tuple)):
            res_args = [*res_args, *arg]
        else:
            res_args.append(arg)
    res_kwargs.update(kwargs)
    return url_for(*res_args, **res_kwargs)
