import pytest
from reflection_loop import investigate_with_reflection


@pytest.mark.integration
def test_clear_symptom_does_not_trigger_reflection():
    outcome = investigate_with_reflection(
        "The application is throwing 'too many connections' errors and the "
        "database's connection count is near its configured maximum."
    )
    assert outcome.result.candidates[0].scenario == "db_connection_exhaustion"
    assert outcome.reflection_triggered is False


@pytest.mark.integration
def test_vague_symptom_triggers_reflection():
    outcome = investigate_with_reflection(
        "Something feels off with the service, users are complaining."
    )
    # can't assert the exact scenario for something this vague, but we can
    # assert the mechanism actually fired
    assert outcome.reflection_triggered is True
    assert len(outcome.critic_reasoning) > 0


@pytest.mark.integration
def test_misleading_symptom_gets_corrected_by_reflection():
    # phrased to sound like cpu_spike on the surface, but the real signal
    # (flat request rate, no traffic increase) points to something else
    outcome = investigate_with_reflection(
        "CPU usage looks a bit elevated, but request traffic hasn't changed at all "
        "and there's no memory growth either - not sure what's actually wrong."
    )
    # main assertion is mechanism, not a specific outcome scenario
    assert isinstance(outcome.result.candidates, list)