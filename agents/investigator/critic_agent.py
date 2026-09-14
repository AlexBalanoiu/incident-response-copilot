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

sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from decision_logger import log_decision

APP_NAME = "incident-copilot"


class CriticVerdict(BaseModel):
    supported: bool
    reasoning: str
    refinement_query: str  # empty string if supported == True


INSTRUCTION = """\
You are the Critic for a Kubernetes incident response system. You do NOT
investigate - you are given a symptom description, the raw evidence that
was retrieved from the knowledge base, and the Investigator's top root
cause candidate. Your job is to judge, skeptically, whether the retrieved
evidence actually supports that specific conclusion.

Common failure to catch: the Investigator picks a plausible-sounding cause
that isn't actually backed by the retrieved text, or picks it despite the
retrieved evidence being about a different scenario entirely.

If the evidence genuinely supports the candidate, mark it supported.
If it's a weak, generic, or mismatched match, mark it unsupported and
write a refinement_query - a more specific or differently-phrased search
query that might surface better evidence than the original query did.

End your reply with ONLY a fenced json block:

```json
{
  "supported": true,
  "reasoning": "<why the evidence does or doesn't support the candidate>",
  "refinement_query": "<only if supported is false, else empty string>"
}
```
"""

critic_agent = LlmAgent(
    name="critic_agent",
    model=LiteLlm(model="gemini/gemini-3.5-flash-lite"),
    instruction=INSTRUCTION,
)


def _extract_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in critic output:\n{text}")
    return json.loads(match.group(1))


def run_critique(
    symptom_description: str,
    evidence_text: str,
    top_candidate_scenario: str,
    incident_id: str = "adhoc",
) -> CriticVerdict:
    with log_decision(incident_id, "critic_agent", symptom_description) as outcome:
        runner = InMemoryRunner(agent=critic_agent, app_name=APP_NAME)
        user_id = "local-user"
        session_id = str(uuid.uuid4())

        runner.session_service.create_session_sync(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        prompt = (
            f"Symptom description: {symptom_description}\n\n"
            f"Retrieved evidence:\n{evidence_text}\n\n"
            f"Investigator's top candidate: {top_candidate_scenario}"
        )
        content = types.Content(role="user", parts=[types.Part(text=prompt)])

        final_text = None
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text

        if final_text is None:
            raise RuntimeError("Critic produced no final response")

        parsed = _extract_json_block(final_text)
        verdict = CriticVerdict(**parsed)
        outcome["output"] = verdict.model_dump()
        return verdict
