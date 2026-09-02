from .base import ReportQuery, SqlReportQuery
from .catalog import QueryCatalog
from .reports import (
    REPORTS,
    LargestAgeDifferenceQuery,
    MixedSexRoomsQuery,
    SmallestAverageAgeQuery,
    StudentsPerRoomQuery,
)

__all__ = [
    "ReportQuery",
    "SqlReportQuery",
    "QueryCatalog",
    "REPORTS",
    "StudentsPerRoomQuery",
    "SmallestAverageAgeQuery",
    "LargestAgeDifferenceQuery",
    "MixedSexRoomsQuery",
]
