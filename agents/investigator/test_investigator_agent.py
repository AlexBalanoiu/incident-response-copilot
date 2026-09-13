import pytest
from investigator_agent import _extract_json_block, run_investigation, InvestigationResult


def test_extract_json_block_parses_valid_output():
    text = (
        "Based on the evidence...\n"
        "```json\n"
        '{"candidates": [{"scenario": "memory_leak", "confidence": 0.8, "reasoning": "linear growth observed"}]}\n'
        "```"
    )
    result = _extract_json_block(text)
    assert result["candidates"][0]["scenario"] == "memory_leak"


def test_extract_json_block_raises_on_missing_block():
    with pytest.raises(ValueError):
        _extract_json_block("No structured output here.")


@pytest.mark.integration
def test_run_investigation_matches_known_scenario():
    result = run_investigation(
        "The application is throwing 'too many connections' errors and the "
        "database's connection count is near its configured maximum."
    )
    assert isinstance(result, InvestigationResult)
    assert len(result.candidates) >= 1
    assert result.candidates[0].scenario == "db_connection_exhaustion"
    assert 0.0 <= result.candidates[0].confidence <= 1.0


@pytest.mark.integration
def test_candidates_are_ranked_by_confidence_descending():
    result = run_investigation(
        "Not sure what's happening — could be slow queries or connection issues, "
        "latency is up and there are occasional connection errors."
    )
    confidences = [c.confidence for c in result.candidates]
    assert confidences == sorted(confidences, reverse=True)