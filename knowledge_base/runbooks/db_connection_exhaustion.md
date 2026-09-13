---
scenario: db_connection_exhaustion
service_type: mysql
---

# DB Connection Exhaustion

## Symptoms
- Application errors: "Too many connections" or connection timeout
- Increased request latency right before errors start
- MySQL `Threads_connected` near `max_connections`

## Likely Causes
- Connection leak in application (connections opened, never returned to pool)
- Pool size misconfigured too low for actual concurrent load
- A single misbehaving client holding many long-lived connections

## Diagnostic Steps
1. PromQL (mysqld_exporter): `mysql_global_status_threads_connected` vs `mysql_global_variables_max_connections` — confirm how close to the ceiling
2. LogQL: `{app="<app>"} |= "too many connections" or "connection timeout"` — confirm error text and timing
3. Check connection pool config in the app (max pool size, idle timeout) against the DB's `max_connections`
4. If possible, correlate with a specific client/pod: which service's connection count grew right before the exhaustion?

## Remediation
- Fix the leak (ensure connections are released/closed, especially in exception paths)
- Right-size the pool relative to `max_connections` and expected concurrency
- Add a connection timeout so a leak degrades gracefully instead of exhausting the pool