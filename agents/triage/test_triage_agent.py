import pytest
from triage_agent import _extract_json_block, run_triage, TriageResult


def test_extract_json_block_parses_valid_output():
    text = (
        "Everything looks fine.\n"
        "```json\n"
        '{"service": "none", "severity": "low", "symptom_summary": "No issues found."}\n'
        "```"
    )
    result = _extract_json_block(text)
    assert result["service"] == "none"
    assert result["severity"] == "low"


def test_extract_json_block_raises_on_missing_block():
    with pytest.raises(ValueError):
        _extract_json_block("I looked into it but forgot the format.")


@pytest.mark.integration
def test_run_triage_against_live_cluster():
    result = run_triage(
        "Check the current state of the monitoring namespace and report any issues."
    )
    assert isinstance(result, TriageResult)
    assert result.severity in {"low", "medium", "high", "critical"}
    assert len(result.symptom_summary) > 0