import json
import re
import uuid

from pydantic import BaseModel, ValidationError
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

from retrieval_tool import search_knowledge_base

APP_NAME = "incident-copilot"


class RootCauseCandidate(BaseModel):
    scenario: str
    confidence: float  # 0.0 - 1.0
    reasoning: str


class InvestigationResult(BaseModel):
    candidates: list[RootCauseCandidate]  # ranked, highest confidence first


INSTRUCTION = """\
You are the Investigator Agent for a Kubernetes incident response system.

Given a symptom description (from the Triage Agent or provided directly),
use the search_knowledge_base tool to retrieve relevant runbooks and past
resolved incidents. Base your conclusions on what the tool actually returns
- do not invent root causes unsupported by retrieved evidence.

After investigating, respond with a short explanation, then end your reply
with ONLY a fenced json block in exactly this shape, ranked highest
confidence first, listing up to 3 candidates:

```json
{
  "candidates": [
    {"scenario": "<scenario name from retrieved results>",
     "confidence": <float 0.0-1.0>,
     "reasoning": "<why this evidence supports this cause>"}
  ]
}
```

If retrieved evidence is weak or contradictory, reflect that with lower
confidence scores rather than forcing a single confident answer.
"""

investigator_agent = LlmAgent(
    name="investigator_agent",
    model=LiteLlm(model="gemini/gemini-3.5-flash-lite"),
    instruction=INSTRUCTION,
    tools=[search_knowledge_base],
)


def _extract_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in agent output:\n{text}")
    return json.loads(match.group(1))


def run_investigation(symptom_description: str) -> InvestigationResult:
    runner = InMemoryRunner(agent=investigator_agent, app_name=APP_NAME)
    user_id = "local-user"
    session_id = str(uuid.uuid4())

    runner.session_service.create_session_sync(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=symptom_description)])

    final_text = None
    for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text

    if final_text is None:
        raise RuntimeError("Agent produced no final response")

    parsed = _extract_json_block(final_text)
    return InvestigationResult(**parsed)