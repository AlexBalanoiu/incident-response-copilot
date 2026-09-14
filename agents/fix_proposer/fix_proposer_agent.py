import json
import re
import sys
import uuid
from pathlib import Path

from pydantic import BaseModel
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent.parent / "investigator"))
from retrieval_tool import search_knowledge_base  # reuse, don't duplicate

from safety_policy import validate_fix_safety

sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from decision_logger import log_decision

APP_NAME = "incident-copilot"


class FixProposal(BaseModel):
    fix_steps: list[str]
    suggested_yaml: str  # empty string if no manifest change needed
    safety_status: str   # must be "safe" - enforced below, not just trusted
    rationale: str


INSTRUCTION = """\
You are the Fix-Proposer Agent for a Kubernetes incident response system.
You NEVER execute anything - you only propose fixes for a human to apply.

Given a root cause (from the Investigator), use search_knowledge_base to
find the relevant runbook's Remediation section, then draft a concrete fix:
- Prefer dry-run forms of commands (e.g. `kubectl rollout undo --dry-run=client`,
  `kubectl apply --dry-run=client`) over anything that mutates state directly.
- If a manifest change is the fix (e.g. adding resource limits, a probe
  timeout, a sizeLimit), include it as YAML.

Before finalizing, you MUST call validate_fix_safety on your complete draft
(fix steps text + yaml combined). If it returns "unsafe", revise your
proposal to remove the offending action and check again. Do not finalize
a proposal that has not passed this check.

End your reply with ONLY a fenced json block in exactly this shape:

```json
{
  "fix_steps": ["<step 1>", "<step 2>", ...],
  "suggested_yaml": "<yaml as a string, or empty string if none>",
  "safety_status": "safe",
  "rationale": "<why this fix addresses the root cause>"
}
```
"""

fix_proposer_agent = LlmAgent(
    name="fix_proposer_agent",
    model=LiteLlm(model="gemini/gemini-3.5-flash-lite"),
    instruction=INSTRUCTION,
    tools=[search_knowledge_base, validate_fix_safety],
)


def _extract_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in agent output:\n{text}")
    return json.loads(match.group(1))


def run_fix_proposer(root_cause_description: str, incident_id: str = "adhoc") -> FixProposal:
    with log_decision(incident_id, "fix_proposer_agent", root_cause_description) as outcome:
        runner = InMemoryRunner(agent=fix_proposer_agent, app_name=APP_NAME)
        user_id = "local-user"
        session_id = str(uuid.uuid4())

        runner.session_service.create_session_sync(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        content = types.Content(role="user", parts=[types.Part(text=root_cause_description)])

        final_text = None
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text

        if final_text is None:
            raise RuntimeError("Agent produced no final response")

        parsed = _extract_json_block(final_text)
        proposal = FixProposal(**parsed)

        # Do not trust the agent's self-reported safety_status - re-verify
        # deterministically against the actual combined output.
        combined_text = "\n".join(proposal.fix_steps) + "\n" + proposal.suggested_yaml
        check = validate_fix_safety(combined_text)
        if check["status"] != "safe":
            raise ValueError(
                f"Agent's final proposal failed independent safety check: {check['violations']}"
            )

        outcome["output"] = proposal.model_dump()
        return proposal
