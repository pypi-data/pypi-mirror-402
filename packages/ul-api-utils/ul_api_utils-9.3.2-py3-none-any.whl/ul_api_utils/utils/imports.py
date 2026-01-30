import sys


def has_already_imported(module_name: str) -> bool:
    return module_name in sys.modules


_has_already_imported_db = False


def has_already_imported_db() -> bool:
    global _has_already_imported_db
    if _has_already_imported_db:
        return True
    _has_already_imported_db = has_already_imported('flask_sqlalchemy')
    return _has_already_imported_db
