### Measured plans

PostgreSQL 16 (official image, default `shared_buffers`/`work_mem`), 1 000 rooms
and 10 000 students, median of five runs. Statistics fresh (`ANALYZE` before
measuring); every planner setting at its default, confirmed by `SETTINGS` in the
`EXPLAIN` output. 

Steady state, after `VACUUM ANALYZE`:

| Report | Students scan | Join | Aggregate | Sort | Buffers |
| --- | --- | --- | --- | --- | --- |
| 1 — students per room | Seq Scan | Hash Right Join | HashAggregate | quicksort 103 kB | 85 |
| 2 — smallest average age | Seq Scan | Hash Join | HashAggregate | top-N heapsort 25 kB | 82 |
| 3 — largest age difference | Seq Scan | Hash Join | HashAggregate | top-N heapsort 25 kB | 82 |
| 4 — mixed-sex rooms | **Index Only Scan**, `Heap Fetches: 0` | **Merge Join** | **GroupAggregate** | **none** | **40** |
