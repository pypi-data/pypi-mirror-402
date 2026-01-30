from typing import Iterable, Any, Optional, Iterator

import math


class ApiPagination:
    def __init__(self, page: int, per_page: int, total: int, items: Iterable[Any]) -> None:
        self.query = None
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self) -> int:
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(math.ceil(self.total / float(self.per_page)))
        return pages

    @property
    def prev_num(self) -> Optional[int]:
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self) -> bool:
        """True if a previous page exists"""
        return self.page > 1

    def prev(self, error_out: bool = False) -> None:
        raise AssertionError('a query object is required for this method to work')

    def next(self, error_out: bool = False) -> None:
        raise AssertionError('a query object is required for this method to work')

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def next_num(self) -> Optional[int]:
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(self, left_edge: int = 2, left_current: int = 2, right_current: int = 5, right_edge: int = 2) -> Iterator[Optional[int]]:
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or (num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
