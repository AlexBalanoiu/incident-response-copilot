import time
import requests

def run(target_url: str, duration_seconds: int = 90, interval_seconds: float = 1.0, **kwargs) -> dict:
    """
    Repeatedly hits /debug/leak on the target app to drive unbounded
    in-memory growth (app-level leak, no eviction policy).
    """
    calls = 0
    start = time.monotonic()
    last_response = None

    while time.monotonic() - start < duration_seconds:
        resp = requests.get(f"{target_url}/debug/leak", timeout=5)
        resp.raise_for_status()
        last_response = resp.json()
        calls += 1
        time.sleep(interval_seconds)

    return {
        "calls_made": calls,
        "final_leaked_mb": last_response.get("leaked_mb") if last_response else None,
        "mechanism": "unbounded in-memory allocation via /debug/leak",
    }