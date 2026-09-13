import pytest
from fix_proposer_agent import _extract_json_block, run_fix_proposer, FixProposal
from safety_policy import validate_fix_safety


def test_extract_json_block_parses_valid_output():
    text = (
        "Here's the fix.\n"
        "```json\n"
        '{"fix_steps": ["step1"], "suggested_yaml": "", "safety_status": "safe", "rationale": "r"}\n'
        "```"
    )
    result = _extract_json_block(text)
    assert result["safety_status"] == "safe"


@pytest.mark.integration
def test_run_fix_proposer_for_memory_leak_returns_safe_proposal():
    proposal = run_fix_proposer(
        "Root cause: memory leak from an unbounded in-memory cache with no eviction policy "
        "on the api-service pod."
    )
    assert isinstance(proposal, FixProposal)
    assert len(proposal.fix_steps) > 0

    # independent re-check, same as the function does internally -
    # this is the test that would actually catch a regression
    combined = "\n".join(proposal.fix_steps) + "\n" + proposal.suggested_yaml
    check = validate_fix_safety(combined)
    assert check["status"] == "safe"


@pytest.mark.integration
def test_run_fix_proposer_for_db_exhaustion_mentions_pool_or_connection():
    proposal = run_fix_proposer(
        "Root cause: connection leak - exception path skips closing the DB connection, "
        "Threads_connected is near max_connections."
    )
    combined_text = " ".join(proposal.fix_steps).lower()
    assert "connection" in combined_text or "pool" in combined_text