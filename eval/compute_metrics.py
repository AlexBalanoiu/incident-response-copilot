import json
from pathlib import Path

DATASET_FILE = Path(__file__).parent / "golden_dataset.jsonl"

# crude keyword check per scenario for "fix relevance" - not semantic, but
# catches the obvious mismatch case (e.g. proposing a pod restart for a slow query)
EXPECTED_FIX_KEYWORDS = {
    "pod_crash": ["probe", "restart", "memory", "limit"],
    "memory_leak": ["cache", "evict", "leak", "release", "cleanup"],
    "db_connection_exhaustion": ["connection", "pool", "close", "leak", "timeout"],
}


def load_dataset() -> list[dict]:
    with open(DATASET_FILE) as f:
        return [json.loads(line) for line in f if line.strip()]


def compute_metrics(dataset: list[dict]) -> dict:
    n = len(dataset)
    if n == 0:
        return {"error": "empty dataset"}

    # Investigator precision@3: is ground truth scenario among top-3 candidates?
    precision_hits = 0
    for row in dataset:
        top3 = [c["scenario"] for c in row["investigator_candidates"][:3]]
        if row["ground_truth_scenario"] in top3:
            precision_hits += 1

    # Investigator top-1 accuracy (stricter, worth reporting alongside precision@3)
    top1_hits = sum(
        1 for row in dataset
        if row["investigator_candidates"] and row["investigator_candidates"][0]["scenario"] == row["ground_truth_scenario"]
    )

    hallucination_count = sum(1 for row in dataset if row["hallucinated_top_candidate"])

    fix_relevant_count = 0
    for row in dataset:
        expected_keywords = EXPECTED_FIX_KEYWORDS.get(row["ground_truth_scenario"], [])
        fix_text = " ".join(row["fix_steps"]).lower()
        if any(kw in fix_text for kw in expected_keywords):
            fix_relevant_count += 1

    reflection_triggered_count = sum(1 for row in dataset if row["reflection_triggered"])

    return {
        "total_incidents": n,
        "investigator_precision_at_3": round(precision_hits / n, 3),
        "investigator_top1_accuracy": round(top1_hits / n, 3),
        "hallucination_rate": round(hallucination_count / n, 3),
        "fix_relevance_rate": round(fix_relevant_count / n, 3),
        "reflection_trigger_rate": round(reflection_triggered_count / n, 3),
    }


if __name__ == "__main__":
    dataset = load_dataset()
    metrics = compute_metrics(dataset)
    print(json.dumps(metrics, indent=2))