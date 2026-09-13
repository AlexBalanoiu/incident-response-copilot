---
scenario: slow_query
service_type: mysql
---

# Slow Query

## Symptoms
- Increased request latency
- CPU and memory on the app pod remain normal (rules out app-side resource issues)
- DB query duration metrics elevated

## Likely Causes
- Missing or ineffective index on a frequently-run query
- Full table scan triggered by a query pattern change
- Lock contention from a concurrent long-running transaction

## Diagnostic Steps
1. PromQL: `mysql_perf_schema_events_statements_avg_time` or query-duration histogram if exported — identify which query class is slow
2. LogQL: check for MySQL slow query log entries if shipped to Loki
3. Compare CPU/memory of the app pod (should be normal) vs DB pod (may be elevated) — confirms it's DB-side, not app-side
4. `EXPLAIN` the suspected query if you can get a shell — look for full table scans

## Remediation
- Add the missing index
- Rewrite the query to avoid the scan pattern
- If lock contention: identify and shorten the blocking transaction