import argparse
import json
from pathlib import Path
from pipeline_runner import run_full_pipeline
from port_forward_manager import ensure_api_service_reachable

OUTPUT_FILE = Path(__file__).parent / "golden_dataset.jsonl"

RUNS_PER_SCENARIO = 4

SCENARIO_CONFIGS = {
    "pod_crash": {
        "target": "api-service",
        "severity": "high",
        "chaos_kwargs": {"target_namespace": "incident-copilot", "target_label_selector": "app=api-service"},
    },
    "memory_leak": {
        "target": "api-service",
        "severity": "medium",
        "chaos_kwargs": {"target_url": "http://localhost:5000", "duration_seconds": 40, "interval_seconds": 1.0},
    },
    "db_connection_exhaustion": {
        "target": "mysql",
        "severity": "high",
        "chaos_kwargs": {
            "db_host": "localhost", "db_user": "root", "db_password": "changeme",
            "db_name": "appdb", "num_connections": 20, "duration_seconds": 40,
        },
    },
}


def main():
    parser = argparse.ArgumentParser(description="Run chaos scenarios through the full agent pipeline.")
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_CONFIGS),
        help="Run only this scenario instead of all of them. Useful for spacing "
             "runs out across free-tier Gemini rate limits.",
    )
    args = parser.parse_args()

    scenarios_to_run = {args.scenario: SCENARIO_CONFIGS[args.scenario]} if args.scenario else SCENARIO_CONFIGS

    written = 0
    # append, not overwrite - so results from a previous --scenario invocation
    # (or an earlier run that got partway through) aren't discarded.
    with open(OUTPUT_FILE, "a") as f:
        for scenario, config in scenarios_to_run.items():
            for run_num in range(RUNS_PER_SCENARIO):
                print(f"Running {scenario} ({run_num + 1}/{RUNS_PER_SCENARIO})...")
                ensure_api_service_reachable()
                try:
                    result = run_full_pipeline(scenario, config["target"], config["severity"], config["chaos_kwargs"])
                    f.write(json.dumps(result) + "\n")
                    f.flush()
                    written += 1
                    print(f"  -> ground truth: {result['ground_truth_scenario']}, "
                          f"top candidate: {result['investigator_candidates'][0]['scenario'] if result['investigator_candidates'] else 'none'}")
                except Exception as e:
                    print(f"  FAILED: {e}")

    print(f"\nWrote {written} incidents to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
