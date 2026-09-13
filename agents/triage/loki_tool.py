import time
import requests

LOKI_URL = "http://localhost:3100"


def query_loki(logql: str, minutes_back: int = 15, limit: int = 100, timeout: float = 5.0) -> dict:
    """
    Run a LogQL range query over the last `minutes_back` minutes.

    Returns:
        {
          "status": "success" | "error",
          "results": [{"stream": {...labels}, "entries": [{"ts": <ns str>, "line": <str>}, ...]}, ...],
          "error": <str, only if status == "error">
        }
    """
    now_ns = time.time_ns()
    start_ns = now_ns - (minutes_back * 60 * 1_000_000_000)

    try:
        resp = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": logql,
                "start": start_ns,
                "end": now_ns,
                "limit": limit,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}

    if payload.get("status") != "success":
        return {"status": "error", "error": payload.get("error", "unknown error")}

    data = payload["data"]
    results = []
    for stream in data.get("result", []):
        entries = [{"ts": ts, "line": line} for ts, line in stream.get("values", [])]
        results.append({"stream": stream.get("stream", {}), "entries": entries})

    return {"status": "success", "results": results}