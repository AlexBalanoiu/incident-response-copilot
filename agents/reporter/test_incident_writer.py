import json
import shutil
import pytest
from pathlib import Path

import incident_writer


@pytest.fixture
def isolated_history(tmp_path, monkeypatch):
    history_file = tmp_path / "incidents.jsonl"
    history_file.write_text('{"incident_id": "inc-0018", "scenario": "disk_pressure", "service": "x", "timestamp": "t", "symptoms_observed": "s", "root_cause": "r", "fix_applied": "f", "resolution_time_minutes": 1}\n')
    monkeypatch.setattr(incident_writer, "HISTORY_FILE", history_file)
    return history_file


def test_next_incident_id_increments_past_existing(isolated_history):
    assert incident_writer._next_incident_id() == "inc-0019"


def test_next_incident_id_starts_at_0001_when_empty(tmp_path, monkeypatch):
    empty_file = tmp_path / "empty.jsonl"
    monkeypatch.setattr(incident_writer, "HISTORY_FILE", empty_file)
    empty_file.write_text("")
    assert incident_writer._next_incident_id() == "inc-0001"