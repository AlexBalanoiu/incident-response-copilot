import json
import re
import uuid

from pydantic import BaseModel, ValidationError
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types

from prometheus_tool import query_prometheus
from loki_tool import query_loki

APP_NAME = "incident-copilot"


class TriageResult(BaseModel):
    service: str
    severity: str  # "low" | "medium" | "high" | "critical"
    symptom_summary: str


INSTRUCTION = """\
You are the Triage Agent for a Kubernetes incident response system.

Given a request to investigate the cluster, use the available tools
(query_prometheus, query_loki) to check current metrics and recent logs.

Prometheus is reachable at http://localhost:9090 and Loki at
http://localhost:3100 — the tools handle the HTTP calls, you just supply
the PromQL / LogQL query strings.

Useful starting queries:
- PromQL "up" to see which targets are down
- LogQL '{namespace="monitoring"}' (or another namespace) to see recent logs

After investigating, respond with a short explanation, then end your
reply with ONLY a fenced json block in exactly this shape:

```json
{
  "service": "<affected service or component name>",
  "severity": "low" | "medium" | "high" | "critical",
  "symptom_summary": "<one or two sentence summary of what you observed>"
}
```

If nothing looks wrong, service can be "none" and severity "low".
"""

triage_agent = LlmAgent(
    name="triage_agent",
    model=LiteLlm(model="gemini/gemini-3.5-flash-lite"),
    instruction=INSTRUCTION,
    tools=[query_prometheus, query_loki],
)


def _extract_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON block found in agent output:\n{text}")
    return json.loads(match.group(1))


def run_triage(user_message: str) -> TriageResult:
    runner = InMemoryRunner(agent=triage_agent, app_name=APP_NAME)
    user_id = "local-user"
    session_id = str(uuid.uuid4())

    runner.session_service.create_session_sync(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    final_text = None
    for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text

    if final_text is None:
        raise RuntimeError("Agent produced no final response")

    parsed = _extract_json_block(final_text)
    return TriageResult(**parsed)