---
scenario: cpu_spike
service_type: generic
---

# CPU Spike

## Symptoms
- Sustained high CPU utilization on one or more pods
- Increased request latency without a proportional increase in traffic
- No corresponding memory growth (rules out a leak-driven spiral)

## Likely Causes
- Inefficient code path triggered by specific input (e.g. unbounded loop, bad regex)
- Missing CPU limits allowing one pod to starve others on the node
- Legitimate traffic increase (not an incident — check request rate first)

## Diagnostic Steps
1. PromQL: `rate(container_cpu_usage_seconds_total{pod="<pod>"}[5m])` — confirm spike magnitude and duration
2. PromQL: `rate(http_requests_total{pod="<pod>"}[5m])` (or equivalent) — check if request rate also rose; if not, it's not traffic-driven
3. LogQL: `{pod="<pod>"}` — look for repeated identical requests or error loops around the spike start
4. Check CPU limits: `kubectl describe pod <pod>` — was the pod already at its CPU limit (throttled) or is the node itself saturated?

## Remediation
- If code-path issue: identify and patch the trigger; short-term, scale horizontally to spread load
- If missing limits: set `resources.limits.cpu` to prevent noisy-neighbor effects
- If legitimate traffic: not an incident, consider autoscaling