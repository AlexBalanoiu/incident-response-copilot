import argparse
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

from scenarios import pod_crash, memory_leak, db_connection_exhaustion

CHAOS_LOG = Path(__file__).parent.parent / "logs" / "chaos_incidents.jsonl"

SCENARIOS = {
    "pod_crash": pod_crash.run,
    "memory_leak": memory_leak.run,
    "db_connection_exhaustion": db_connection_exhaustion.run,
}

GROUND_TRUTH_CAUSE = {
    "pod_crash": "External kill / forced pod deletion",
    "memory_leak": "Application-level memory leak (unbounded allocation, no eviction)",
    "db_connection_exhaustion": "Connection leak - opened connections held without being released",
}


def trigger_incident(scenario: str, target: str, severity: str = "medium", **scenario_kwargs) -> dict:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}', choose from {list(SCENARIOS)}")

    incident_id = f"chaos-{uuid.uuid4().hex[:8]}"
    start_time = datetime.now(timezone.utc).isoformat()

    result = SCENARIOS[scenario](**scenario_kwargs)

    record = {
        "incident_id": incident_id,
        "scenario": scenario,
        "target": target,
        "severity": severity,
        "start_time": start_time,
        "ground_truth_cause": GROUND_TRUTH_CAUSE[scenario],
        "scenario_result": result,
    }

    CHAOS_LOG.parent.mkdir(exist_ok=True)
    with open(CHAOS_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=list(SCENARIOS))
    parser.add_argument("--target", required=True)
    parser.add_argument("--severity", default="medium")
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()

    kwargs = {"duration_seconds": args.duration}
    if args.scenario == "pod_crash":
        kwargs = {"target_namespace": "incident-copilot", "target_label_selector": f"app={args.target}"}
    elif args.scenario == "memory_leak":
        kwargs["target_url"] = "http://localhost:5000"
    elif args.scenario == "db_connection_exhaustion":
        kwargs.update({"db_host": "localhost", "db_user": "root", "db_password": "changeme", "db_name": "appdb"})

    record = trigger_incident(args.scenario, args.target, args.severity, **kwargs)
    print(json.dumps(record, indent=2))