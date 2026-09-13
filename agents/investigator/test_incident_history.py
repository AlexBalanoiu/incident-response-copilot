import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent.parent.parent / "knowledge_base" / "incident_history" / "incidents.jsonl"
VALID_SCENARIOS = {
    "pod_crash", "cpu_spike", "memory_leak",
    "db_connection_exhaustion", "slow_query", "disk_pressure",
}
REQUIRED_FIELDS = {
    "incident_id", "scenario", "service", "timestamp",
    "symptoms_observed", "root_cause", "fix_applied", "resolution_time_minutes",
}


def _load_incidents():
    with open(HISTORY_FILE) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_minimum_incident_count():
    incidents = _load_incidents()
    assert len(incidents) >= 15


def test_every_scenario_represented():
    incidents = _load_incidents()
    found_scenarios = {i["scenario"] for i in incidents}
    assert found_scenarios == VALID_SCENARIOS


def test_incident_ids_unique():
    incidents = _load_incidents()
    ids = [i["incident_id"] for i in incidents]
    assert len(ids) == len(set(ids))


def test_all_required_fields_present():
    incidents = _load_incidents()
    for i in incidents:
        assert REQUIRED_FIELDS.issubset(i.keys()), f"{i['incident_id']} missing fields"
        assert i["scenario"] in VALID_SCENARIOS
        assert isinstance(i["resolution_time_minutes"], int)