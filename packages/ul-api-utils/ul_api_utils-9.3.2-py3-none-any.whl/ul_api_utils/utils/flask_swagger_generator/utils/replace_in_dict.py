from typing import Union, List, Dict


def replace_value_in_dict(item: Union[List, Dict], original_schema):  # type: ignore
    if isinstance(item, list):
        return [replace_value_in_dict(i, original_schema) for i in item]
    elif isinstance(item, dict):
        if '$ref' in item:
            definitions = item['$ref'][2:].split('/')
            res = original_schema
            try:
                for definition in definitions:
                    res = res[definition]
            except (KeyError, TypeError):
                return item
            if res is None:
                return None
            return replace_value_in_dict(res, original_schema)
        else:
            return {key: replace_value_in_dict(i, original_schema) for key, i in item.items()}
    else:
        return item  # type: ignore
