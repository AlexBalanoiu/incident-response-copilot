import json
import pytest
from decision_logger import log_decision


@pytest.fixture
def isolated_log(tmp_path, monkeypatch):
    import decision_logger
    log_file = tmp_path / "decisions.jsonl"
    monkeypatch.setattr(decision_logger, "LOG_FILE", log_file)
    return log_file


def test_log_decision_writes_one_line_with_expected_fields(isolated_log):
    with log_decision("inc-test", "triage_agent", "check the cluster") as outcome:
        outcome["output"] = {"service": "api", "severity": "low"}
        outcome["input_tokens"] = 50
        outcome["output_tokens"] = 20

    lines = isolated_log.read_text().strip().split("\n")
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["incident_id"] == "inc-test"
    assert record["agent"] == "triage_agent"
    assert record["latency_seconds"] >= 0
    assert record["input_tokens"] == 50
    assert record["estimated_cost_usd"] > 0


def test_log_decision_still_writes_on_exception(isolated_log):
    with pytest.raises(ValueError):
        with log_decision("inc-test2", "investigator_agent", "vague input") as outcome:
            raise ValueError("simulated agent failure")

    lines = isolated_log.read_text().strip().split("\n")
    assert len(lines) == 1  # log entry written even though the block raised