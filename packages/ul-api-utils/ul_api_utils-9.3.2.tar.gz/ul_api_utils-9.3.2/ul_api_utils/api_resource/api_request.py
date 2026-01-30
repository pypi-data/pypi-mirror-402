import json
from typing import NamedTuple, Iterable, Any, List, Tuple, Dict, Optional

from flask_sqlalchemy.query import Query
from pydantic import model_validator, BaseModel

from ul_api_utils.errors import SimpleValidateApiError
from ul_api_utils.utils.api_pagination import ApiPagination
from ul_api_utils.utils.imports import has_already_imported_db


class ApiRequestQueryPagination(NamedTuple):
    page: int
    limit: int
    offset: int
    per_page: int

    def mk_item_pagination(self, items: Iterable[Any], total: int) -> ApiPagination:
        return ApiPagination(
            total=total,
            per_page=self.per_page,
            page=self.page,
            items=items,
        )

    # TODO: Not sure that is worked. Check it if will be found usages
    def mk_sqlalchemy_pagination(self, items: Iterable[Any], total: int, query: Any = None) -> 'ApiPagination':
        if has_already_imported_db() and query:
            return query.paginate(total=total, query=query, per_page=self.per_page, page=self.page, items=items)  # type: ignore
        return self.mk_item_pagination(items, total)


class ApiRequestQuerySortBy(NamedTuple):
    params: List[Tuple[str, str]]


class ApiRequestQueryFilterBy(NamedTuple):
    params: List[Dict[str, Any]]


class ApiRequestQuery(BaseModel):
    sort: Optional[str] = None
    filter: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    page: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def validate_empty_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        vals = dict()
        for k, v in values.items():
            vals[k] = v if v != "" else None
        return vals

    def pagination(self, default_limit: int, max_limit: int) -> ApiRequestQueryPagination:
        try:
            offset = max(int(self.offset or '0'), 0)
        except Exception:  # noqa: B902
            offset = 0

        try:
            limit = min(max(int(self.limit or str(default_limit)), 0), max_limit)
        except Exception:  # noqa: B902
            limit = default_limit

        try:
            page = max(int(self.page or '1'), 1)
        except Exception:  # noqa: B902
            page = 1

        if self.page is not None:
            offset = limit * (page - 1)
        else:
            page = int(offset / limit) + 1

        return ApiRequestQueryPagination(
            limit=limit,
            offset=offset,
            page=page,
            per_page=limit,
        )

    def filter_by(self, attr: str = "filter") -> List[Dict[str, Any]]:
        filter_value = getattr(self, attr)
        if not filter_value:
            return []
        _filter_by = json.loads(filter_value)
        if not all([isinstance(filter_arg, dict) for filter_arg in _filter_by]):
            raise SimpleValidateApiError('invalid filters format')
        return _filter_by

    def sort_by(self, attr: str = "sort") -> List[Tuple[str, str]]:
        sort_value = getattr(self, attr)
        _sort_by: List[Tuple[str, str]] = []
        if not sort_value or not sort_value.strip():
            return _sort_by
        for _sort_arg in sort_value.strip().split(' '):
            if not _sort_arg:
                continue
            if _sort_arg.startswith("+") or _sort_arg.startswith("-"):
                _sort_by.append((_sort_arg[0], _sort_arg[1:]))
            else:
                _sort_by.append(("+", _sort_arg))
        return _sort_by
