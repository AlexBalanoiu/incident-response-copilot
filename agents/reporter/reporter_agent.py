import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from decision_logger import log_decision

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
APP_NAME = "incident-copilot"


INSTRUCTION = """\
You are the Reporter Agent for a Kubernetes incident response system.
You will be given the full pipeline output: Triage result, Investigator's
root cause candidates, and the Fix-Proposer's proposal. Write a clear,
concise postmortem in Markdown with these sections:

## Summary
## Timeline
## Root Cause
## Fix Applied
## Prevention

Be factual and reference only what was actually reported by the other
agents - do not add causes, evidence, or fixes not present in the input.
Output ONLY the markdown report, no preamble.
"""

reporter_agent = LlmAgent(
    name="reporter_agent",
    model=LiteLlm(model="gemini/gemini-3.5-flash-lite"),
    instruction=INSTRUCTION,
)


def generate_report(pipeline_summary: str, incident_id: str) -> Path:
    with log_decision(incident_id, "reporter_agent", pipeline_summary) as outcome:
        runner = InMemoryRunner(agent=reporter_agent, app_name=APP_NAME)
        user_id = "local-user"
        session_id = str(uuid.uuid4())

        runner.session_service.create_session_sync(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        content = types.Content(role="user", parts=[types.Part(text=pipeline_summary)])

        final_text = None
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text

        if final_text is None:
            raise RuntimeError("Agent produced no final response")

        REPORTS_DIR.mkdir(exist_ok=True)
        report_path = REPORTS_DIR / f"{incident_id}.md"
        report_path.write_text(final_text)
        outcome["output"] = str(report_path)
        return report_path
