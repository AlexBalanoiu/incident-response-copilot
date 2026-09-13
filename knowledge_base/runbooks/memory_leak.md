---
scenario: memory_leak
service_type: generic
---

# Memory Leak

## Symptoms
- Steady, near-linear memory growth over time (not a step change)
- Eventually ends in OOMKilled (see `pod_crash.md` for the crash side of this)
- No corresponding increase in traffic or workload size

## Likely Causes
- Application-level leak (unbounded cache, unclosed connections/handles, growing in-memory collection)
- Large object retention across requests (e.g. accumulating request/response bodies)

## Diagnostic Steps
1. PromQL: `container_memory_working_set_bytes{pod="<pod>"}` over a wide time range — confirm linear (not sawtooth) growth pattern
2. Compare growth rate to request rate: `rate(http_requests_total{pod="<pod>"}[5m])` — if requests are flat but memory keeps climbing, it's leak-shaped, not load-shaped
3. LogQL: `{pod="<pod>"}` — check for repeated allocation-related log lines if the app logs them
4. Note the deploy/restart time vs when growth started — did it begin right after a specific deploy?

## Remediation
- Identify and fix the retention point in code (cache eviction policy, connection pooling, explicit cleanup)
- Short-term mitigation: scheduled pod restarts (not a fix, buys time)