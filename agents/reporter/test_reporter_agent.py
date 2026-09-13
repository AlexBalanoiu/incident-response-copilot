import pytest
from reporter_agent import generate_report
from incident_writer import append_incident_record


@pytest.mark.integration
def test_full_writeback_and_report_cycle():
    record = append_incident_record(
        scenario="cpu_spike",
        service="test-service",
        timestamp="2026-09-13T12:00:00Z",
        symptoms_observed="CPU pinned at 100% for 15 minutes, request latency tripled.",
        root_cause="Inefficient regex causing catastrophic backtracking.",
        fix_applied="Rewrote the regex, added a request size guard.",
        resolution_time_minutes=30,
    )
    assert record["incident_id"].startswith("inc-")

    summary = (
        f"Triage: severity high, service test-service.\n"
        f"Investigator root cause: {record['root_cause']}\n"
        f"Fix proposed: {record['fix_applied']}\n"
    )
    report_path = generate_report(summary, record["incident_id"])
    assert report_path.exists()

    text = report_path.read_text()
    for section in ["## Summary", "## Timeline", "## Root Cause", "## Fix Applied", "## Prevention"]:
        assert section in text


@pytest.mark.integration
def test_writeback_is_immediately_retrievable():
    # confirms the memory effect (2.2): a freshly written incident must be
    # findable right away, not just after a full re-ingest
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "investigator"))
    from retrieval_tool import search_knowledge_base

    record = append_incident_record(
        scenario="disk_pressure",
        service="unique-marker-service-xyz",
        timestamp="2026-09-13T13:00:00Z",
        symptoms_observed="Extremely rare marker phrase: zzqrst disk fill event.",
        root_cause="Malformed request triggered infinite write loop.",
        fix_applied="Added input validation and write-size cap.",
        resolution_time_minutes=45,
    )
    result = search_knowledge_base("zzqrst disk fill event", n_results=3)
    scenarios = [r["scenario"] for r in result["results"]]
    assert record["scenario"] in scenarios