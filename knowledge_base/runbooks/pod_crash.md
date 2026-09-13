---
scenario: pod_crash
service_type: generic
---

# Pod Crash

## Symptoms
- Pod restart count increasing
- Gap in application logs around restart time
- `kubectl get events` shows `Killing` / `Started` pairs close together

## Likely Causes
- OOMKilled (check `kubectl describe pod` for `OOMKilled` reason, exit code 137)
- Liveness probe failing repeatedly
- External kill (manual deletion, node eviction)
- Unhandled application crash (check exit code, should be non-zero and non-137)

## Diagnostic Steps
1. `kubectl describe pod <pod>` — check `Last State` reason and exit code
2. PromQL: `kube_pod_container_status_restarts_total` — confirm restart count and timing
3. LogQL: `{pod="<pod>"} |= "panic" or "fatal" or "OOM"` — look for crash signal in the last log lines before the gap
4. Cross-check timing: does the crash correlate with a memory metric spike (points to OOM) or is it isolated (points to external kill or probe failure)?

## Remediation
- If OOMKilled: increase memory limit or fix the leak (see `memory_leak.md` if growth was gradual)
- If probe failure: check probe timeout/threshold vs actual startup time
- If external kill: no code fix needed, just confirm intent