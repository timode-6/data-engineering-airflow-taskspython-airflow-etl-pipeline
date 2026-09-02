from __future__ import annotations

from collections.abc import Iterator, Sequence

from .base import ReportQuery


class QueryCatalog:

    def __init__(self, queries: Sequence[ReportQuery]) -> None:
        names = [query.name for query in queries]
        duplicates = {name for name in names if names.count(name) > 1}
        if duplicates:
            raise ValueError(f"Duplicate query names: {', '.join(sorted(duplicates))}")
        for query in queries:
            if not query.sql.strip():
                raise ValueError(f"Query {query.name!r} has no SQL")
        self._queries: tuple[ReportQuery, ...] = tuple(queries)

    def __iter__(self) -> Iterator[ReportQuery]:
        return iter(self._queries)

    def __len__(self) -> int:
        return len(self._queries)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(query.name for query in self._queries)

    def get(self, name: str) -> ReportQuery:
        for query in self._queries:
            if query.name == name:
                return query
        raise KeyError(name)
