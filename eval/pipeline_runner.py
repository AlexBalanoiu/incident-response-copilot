import sys
import time
import threading
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "triage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "investigator"))
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "fix_proposer"))
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "reporter"))
sys.path.insert(0, str(Path(__file__).parent.parent / "chaos-injector"))

from triage_agent import run_triage
from reflection_loop import investigate_with_reflection
from retrieval_tool import search_knowledge_base
from fix_proposer_agent import run_fix_proposer
from reporter_agent import generate_report
from incident_writer import append_incident_record
from cli import trigger_incident


def _run_chaos_background(scenario: str, target: str, severity: str, kwargs: dict) -> tuple[threading.Thread, dict]:
    holder = {}
    def _target():
        holder["record"] = trigger_incident(scenario=scenario, target=target, severity=severity, **kwargs)
    t = threading.Thread(target=_target)
    t.start()
    return t, holder


def run_full_pipeline(scenario: str, target: str, severity: str, chaos_kwargs: dict) -> dict:
    """
    Triggers a chaos scenario, runs it through the full agent pipeline while
    the symptom is still active, and returns a record combining ground truth
    with what each agent actually produced.
    """
    eval_id = f"eval-{uuid.uuid4().hex[:8]}"
    start = time.monotonic()

    if scenario == "pod_crash":
        chaos_record = trigger_incident(scenario=scenario, target=target, severity=severity, **chaos_kwargs)
        time.sleep(10)  # let restart/event show up in metrics+logs before Triage looks
        thread = None
    else:
        thread, holder = _run_chaos_background(scenario, target, severity, chaos_kwargs)
        time.sleep(chaos_kwargs.get("duration_seconds", 60) * 0.4)  # run Triage mid-window, while symptom is active

    triage_result = run_triage(
        f"Check the incident-copilot namespace, focusing on api-service and mysql, "
        f"and report any issues.",
        incident_id=eval_id,
    )

    symptom_desc = f"Service: {triage_result.service}. {triage_result.symptom_summary}"
    reflection_outcome = investigate_with_reflection(symptom_desc)
    investigation = reflection_outcome.result

    evidence = search_knowledge_base(symptom_desc, n_results=5)
    retrieved_scenarios = {r["scenario"] for r in evidence["results"]}

    top_candidate = investigation.candidates[0] if investigation.candidates else None
    hallucinated = (top_candidate is not None) and (top_candidate.scenario not in retrieved_scenarios)

    root_cause_desc = (
        f"Root cause: {top_candidate.scenario} - {top_candidate.reasoning}"
        if top_candidate else "No root cause identified."
    )
    fix_proposal = run_fix_proposer(root_cause_desc, incident_id=eval_id)

    if thread is not None:
        thread.join()  # ensure chaos cleanup (closed connections etc.) completes before we continue
        chaos_record = holder["record"]

    resolution_minutes = round((time.monotonic() - start) / 60, 2)

    written_incident = append_incident_record(
        scenario=top_candidate.scenario if top_candidate else "unknown",
        service=triage_result.service,
        timestamp=datetime.now(timezone.utc).isoformat(),
        symptoms_observed=triage_result.symptom_summary,
        root_cause=root_cause_desc,
        fix_applied="; ".join(fix_proposal.fix_steps),
        resolution_time_minutes=int(resolution_minutes) or 1,
    )

    pipeline_summary = (
        f"Triage: severity {triage_result.service}, {triage_result.symptom_summary}\n"
        f"Investigator top candidate: {top_candidate.scenario if top_candidate else 'none'}\n"
        f"Fix proposed: {'; '.join(fix_proposal.fix_steps)}\n"
    )
    generate_report(pipeline_summary, written_incident["incident_id"])

    return {
        "eval_id": eval_id,
        "ground_truth_scenario": chaos_record["scenario"],
        "ground_truth_severity": chaos_record["severity"],
        "triage_severity": triage_result.severity,  # note: TriageResult has no explicit severity field name clash - see below
        "investigator_candidates": [c.model_dump() for c in investigation.candidates],
        "reflection_triggered": reflection_outcome.reflection_triggered,
        "hallucinated_top_candidate": hallucinated,
        "fix_steps": fix_proposal.fix_steps,
        "resolution_minutes": resolution_minutes,
        "written_incident_id": written_incident["incident_id"],
    }