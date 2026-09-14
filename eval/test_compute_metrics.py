from compute_metrics import compute_metrics


def _fake_row(ground_truth, top_candidates_scenarios, hallucinated, fix_text, reflection=False):
    return {
        "ground_truth_scenario": ground_truth,
        "investigator_candidates": [
            {"scenario": s, "confidence": 0.7, "reasoning": "r"} for s in top_candidates_scenarios
        ],
        "hallucinated_top_candidate": hallucinated,
        "fix_steps": [fix_text],
        "reflection_triggered": reflection,
    }


def test_precision_at_3_counts_ground_truth_anywhere_in_top3():
    dataset = [
        _fake_row("memory_leak", ["cpu_spike", "memory_leak", "slow_query"], False, "add cache eviction"),
        _fake_row("pod_crash", ["disk_pressure", "cpu_spike", "slow_query"], False, "increase probe timeout"),
    ]
    metrics = compute_metrics(dataset)
    assert metrics["investigator_precision_at_3"] == 0.5


def test_top1_accuracy_stricter_than_precision_at_3():
    dataset = [
        _fake_row("memory_leak", ["cpu_spike", "memory_leak"], False, "add cache eviction"),
    ]
    metrics = compute_metrics(dataset)
    assert metrics["investigator_top1_accuracy"] == 0.0
    assert metrics["investigator_precision_at_3"] == 1.0


def test_hallucination_rate():
    dataset = [
        _fake_row("memory_leak", ["memory_leak"], hallucinated=False, fix_text="add eviction"),
        _fake_row("cpu_spike", ["memory_leak"], hallucinated=True, fix_text="add limits"),
    ]
    metrics = compute_metrics(dataset)
    assert metrics["hallucination_rate"] == 0.5


def test_fix_relevance_matches_expected_keywords():
    dataset = [
        _fake_row("db_connection_exhaustion", ["db_connection_exhaustion"], False, "close leaked connections and add pool timeout"),
        _fake_row("db_connection_exhaustion", ["db_connection_exhaustion"], False, "restart the pod"),  # irrelevant fix
    ]
    metrics = compute_metrics(dataset)
    assert metrics["fix_relevance_rate"] == 0.5