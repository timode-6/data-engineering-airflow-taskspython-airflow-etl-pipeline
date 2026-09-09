# Query plans

Measurements behind `src/hostel/sql/indexes.sql`.

**Conditions.** PostgreSQL 16, official Docker image, defaults throughout. 1 000 rooms,
10 000 students, `VACUUM ANALYZE` applied, warm cache. Captured with
`EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)` via `docs/explain/plans.sql`.

Execution times are **not** comparable between runs here — identical plans varied between
5 ms and 13 ms depending on OS cache state. Buffer counts and plan shape are the reliable
measures, so those are what the tables report.

## Results

| Report | Students access | Join | Aggregate | Sort | Buffers |
| --- | --- | --- | --- | --- | --- |
| 1 — students per room | Seq Scan (76 pages) | Hash Right Join | HashAggregate | quicksort 71 kB | 85 |
| 2 — smallest average age | Seq Scan | Hash Join | HashAggregate | top-N heapsort 25 kB | 85 |
| 3 — largest age difference | Seq Scan | Hash Join | HashAggregate | top-N heapsort 25 kB | 82 |
| 4 — mixed-sex rooms | **Index Only Scan**, `Heap Fetches: 0` | **Merge Join** | **GroupAggregate** | **none** | **41** |

`idx_students_room_sex` halves the work for report 4, and the reason is not only the
index-only scan. Entries arrive ordered by `room`, so the join becomes a merge, the
aggregate streams instead of building a hash table, and `ORDER BY r.id` is satisfied by
the input order — the sort node disappears entirely.

## Why reports 1–3 stay on a sequential scan

They select `COUNT(s.id)` originally, and `id` is not in `(room, birthday)`: a PostgreSQL
btree leaf holds the indexed columns plus a tuple pointer and, unlike InnoDB, does not
append the primary key. Referencing `id` therefore forces a heap visit per row.

Changing report 1 to `COUNT(s.room)` and reports 2–3 to `COUNT(*)` removes that
reference — under the `LEFT JOIN`, `s.room` is `NULL` exactly when no student matched, so
it equals `COUNT(s.id)`, while `COUNT(*)` would wrongly report the empty room as having
one resident.

That made an index-only scan *possible*, but the planner still declines it:

| Report 1 access path | Estimated cost |
| --- | --- |
| Seq Scan on students | 176.00 |
| Index Only Scan on `idx_students_room_sex` | 218.28 |

At 76 pages the flat scan is cheaper when every row is needed, and the planner is right.
Reports 2 and 3 additionally order by an aggregate, so pre-sorted input buys them nothing.

## The index that isn't earning its place

```
        indexrelname        | idx_scan | idx_tup_read
----------------------------+----------+--------------
 idx_students_room_birthday |        2 |        20000
 idx_students_room_sex      |       19 |        30016
 students_pkey              |   150000 |       153667
```

`idx_students_room_birthday` has been scanned twice — both times against a bloated table
(see below). On a healthy heap nothing chooses it. It costs a write on every insert and
returns nothing, so **it is not part of the shipped schema.**

`idx_students_room_sex` stays: report 4 depends on it, and report 1 would fall back to it
if the table grew.

## Two things measurement caught that reasoning did not

**Repeated upserts bloat the table.** After 15 import runs the heap had grown from 76 to
297 pages — `ON CONFLICT DO UPDATE` writes a new row version each time and leaves the old
one dead. While bloated, the index-only path looked clearly better (218 vs 397); after
`VACUUM FULL` restored 76 pages, the sequential scan won. **The index appeared valuable
only because the table was four times larger than it should have been.** A scheduled load
needs autovacuum tuning or periodic maintenance.

**An index-only scan with a cold visibility map is worse than no index at all.**
`VACUUM FULL` rewrites the table and leaves the map empty; the scan must then check every
tuple's visibility against the heap:

| Report 4 | `Heap Fetches` | Buffers |
| --- | --- | --- |
| no indexes | — | 322 |
| indexes, visibility map cold | 10 000 | **9 701** |
| indexes, after `VACUUM ANALYZE` | 0 | 41 |

This is why `indexes.sql` ends at `ANALYZE` and the vacuum is a documented manual step:
`VACUUM` cannot run inside a transaction block.

## Two details visible in the plans

**The empty room.** Report 1's join emits 10 001 rows — 10 000 students plus the one room
with no residents, preserved by the `LEFT JOIN`. Reports 2–4 use an inner join and
aggregate 999 groups. The difference between those numbers is the room nobody lives in.

**An estimate the planner cannot make.** Report 4 predicts 333 groups against 990 actual,
and `Rows Removed by Filter: 9`. The selectivity of a `HAVING` clause on an aggregate is
not estimable, so PostgreSQL falls back to a fixed fraction. Harmless here — the plan was
already optimal — but this is the class of misestimate that picks a poor join order on
larger data.

## At this data size

10 000 rows in 76 pages. For reports 1–3 the sequential scan is correct and no index
beats it; the cost model is choosing right, and the measurements confirm it. Only report 4
benefits, because it needs sorted input rather than merely fewer pages. The indexes matter
for plan shape as the table grows — the bloat episode above is an accidental preview of
what that looks like.

## Verified at scale

The `(room, birthday)` index was kept on the expectation that it would win as the
table grew. It was tested at 5 000 000 students:

| Report | Plan at 5M rows | Buffers |
| --- | --- | --- |
| 1 — students per room | Seq Scan, Hash Right Join | 35 802 |
| 2 — smallest average age | **Parallel** Seq Scan, 2 workers | 35 834 |
| 3 — largest age difference | **Parallel** Seq Scan, 2 workers | 35 831 |
| 4 — mixed-sex rooms | Index Only Scan, `Heap Fetches: 0`, Merge Join | **8 170** |

`idx_students_room_birthday` was still never chosen — `idx_scan` stayed at 2 across
the entire exercise. Reports 2 and 3 read every row and order by an aggregate, so
index ordering cannot help them, and the planner prefers splitting a sequential scan
across two parallel workers over walking a 5-million-entry index serially.

Report 4's advantage widened with scale: 2× fewer buffers at 10 000 rows, 4× at
5 million. Dropping the unused index removed 128 MB of storage and one B-tree write
per insert, with no measurable change to any plan.

**The distinction that matters:** an index that merely avoids reading pages can be
beaten by a parallel sequential scan. An index that supplies an *ordering* the query
needs cannot — nothing else can produce sorted input for free.