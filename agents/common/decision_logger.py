import json
import time
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "decisions.jsonl"

# Rough per-1K-token USD estimates for gemini-3.5-flash-lite (update if pricing changes)
INPUT_COST_PER_1K = 0.0001
OUTPUT_COST_PER_1K = 0.0004


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000 * INPUT_COST_PER_1K) + (output_tokens / 1000 * OUTPUT_COST_PER_1K)


@contextmanager
def log_decision(incident_id: str, agent_name: str, input_text: str):
    start = time.monotonic()
    record = {
        "incident_id": incident_id,
        "agent": agent_name,
        "input_preview": input_text[:200],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    outcome = {}
    try:
        yield outcome  # caller fills outcome["output"], optionally outcome["input_tokens"]/["output_tokens"]
    finally:
        record["latency_seconds"] = round(time.monotonic() - start, 3)
        record["output_preview"] = str(outcome.get("output", ""))[:200]
        in_tok = outcome.get("input_tokens", 0)
        out_tok = outcome.get("output_tokens", 0)
        record["input_tokens"] = in_tok
        record["output_tokens"] = out_tok
        record["estimated_cost_usd"] = round(_estimate_cost(in_tok, out_tok), 6)

        LOG_FILE.parent.mkdir(exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")