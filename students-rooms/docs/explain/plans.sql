\echo '=== 1. students per room ==='
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT r.id          AS room_id,
       r.name        AS room_name,
       COUNT(s.room) AS students_count
FROM rooms r
LEFT JOIN students s ON s.room = r.id
GROUP BY r.id, r.name
ORDER BY r.id;

\echo '=== 2. smallest average age ==='
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT r.id     AS room_id,
       r.name   AS room_name,
       COUNT(*) AS students_count,
       ROUND(AVG(CURRENT_DATE - s.birthday) / 365.2425, 2) AS average_age_years
FROM rooms r
JOIN students s ON s.room = r.id
GROUP BY r.id, r.name
ORDER BY AVG(CURRENT_DATE - s.birthday) ASC
LIMIT 5;

\echo '=== 3. largest age difference ==='
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT r.id     AS room_id,
       r.name   AS room_name,
       COUNT(*) AS students_count,
       ROUND((MAX(s.birthday) - MIN(s.birthday)) / 365.2425, 2) AS age_difference_years
FROM rooms r
JOIN students s ON s.room = r.id
GROUP BY r.id, r.name
ORDER BY (MAX(s.birthday) - MIN(s.birthday)) DESC
LIMIT 5;

\echo '=== 4. mixed-sex rooms ==='
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT r.id   AS room_id,
       r.name AS room_name,
       COUNT(*) FILTER (WHERE s.sex = 'M') AS male_count,
       COUNT(*) FILTER (WHERE s.sex = 'F') AS female_count
FROM rooms r
JOIN students s ON s.room = r.id
GROUP BY r.id, r.name
HAVING COUNT(DISTINCT s.sex) > 1
ORDER BY r.id;

\echo '=== index usage so far ==='
SELECT indexrelname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE relname = 'students'
ORDER BY indexrelname;

\echo '=== sizes ==='
SELECT pg_size_pretty(pg_relation_size('students')) AS students_heap,
       pg_size_pretty(pg_total_relation_size('students') - pg_relation_size('students')) AS students_indexes;