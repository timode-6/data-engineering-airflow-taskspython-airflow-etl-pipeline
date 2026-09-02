from __future__ import annotations

from .base import ReportQuery, SqlReportQuery

DAYS_PER_YEAR = "365.2425"


class StudentsPerRoomQuery(SqlReportQuery):
    NAME = "students_per_room"
    SQL = """
        SELECT r.id AS room_id,
               r.name AS room_name,
               COUNT(s.id) AS students_count
        FROM rooms r
        LEFT JOIN students s ON s.room = r.id
        GROUP BY r.id, r.name
        ORDER BY r.id
    """


class SmallestAverageAgeQuery(SqlReportQuery):
    NAME = "rooms_with_smallest_average_age"
    SQL = f"""
        SELECT r.id AS room_id,
               r.name AS room_name,
               COUNT(s.id) AS students_count,
               ROUND(AVG(CURRENT_DATE - s.birthday) / {DAYS_PER_YEAR}, 2) AS average_age_years
        FROM rooms r
        JOIN students s ON s.room = r.id
        GROUP BY r.id, r.name
        ORDER BY AVG(CURRENT_DATE - s.birthday) ASC
        LIMIT 5
    """


class LargestAgeDifferenceQuery(SqlReportQuery):
    NAME = "rooms_with_largest_age_difference"
    SQL = f"""
        SELECT r.id AS room_id,
               r.name AS room_name,
               COUNT(s.id) AS students_count,
               ROUND((MAX(s.birthday) - MIN(s.birthday)) / {DAYS_PER_YEAR}, 2) AS age_difference_years
        FROM rooms r
        JOIN students s ON s.room = r.id
        GROUP BY r.id, r.name
        ORDER BY (MAX(s.birthday) - MIN(s.birthday)) DESC
        LIMIT 5
    """


class MixedSexRoomsQuery(SqlReportQuery):
    NAME = "rooms_with_mixed_sex_students"
    SQL = """
        SELECT r.id AS room_id,
               r.name AS room_name,
               COUNT(*) FILTER (WHERE s.sex = 'M') AS male_count,
               COUNT(*) FILTER (WHERE s.sex = 'F') AS female_count
        FROM rooms r
        JOIN students s ON s.room = r.id
        GROUP BY r.id, r.name
        HAVING COUNT(DISTINCT s.sex) > 1
        ORDER BY r.id
    """


REPORTS: tuple[ReportQuery, ...] = (
    StudentsPerRoomQuery(),
    SmallestAverageAgeQuery(),
    LargestAgeDifferenceQuery(),
    MixedSexRoomsQuery(),
)
