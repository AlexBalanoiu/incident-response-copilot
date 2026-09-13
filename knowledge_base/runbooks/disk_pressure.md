---
scenario: disk_pressure
service_type: generic
---

# Disk Pressure

## Symptoms
- Kubelet eviction events (`DiskPressure` condition on node)
- Pods stuck `Pending` or getting evicted
- Rapid growth in volume usage

## Likely Causes
- Application writing excessive logs/temp files to an `emptyDir` or PVC without cleanup
- A specific job/scenario intentionally filling disk (as in this project's own chaos scenario)
- Missing log rotation

## Diagnostic Steps
1. PromQL: `kubelet_volume_stats_used_bytes` vs `kubelet_volume_stats_capacity_bytes` — confirm which volume is filling and how fast
2. `kubectl describe node <node>` — check for `DiskPressure` condition and recent eviction events
3. LogQL: `{pod="<pod>"}` — look for repeated write operations or errors right before pressure began
4. Identify the specific path/volume responsible (exec into pod if still running, or check volume mounts)

## Remediation
- Add log rotation / cleanup job
- Set a size limit on `emptyDir` (`sizeLimit`) so a runaway write fails fast instead of taking the node down
- If PVC-backed: increase size or add usage alerting before it becomes critical