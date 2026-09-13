import requests

PROMETHEUS_URL = "http://localhost:9090"


def query_prometheus(promql: str, timeout: float = 5.0) -> dict:
    """
    Run an instant PromQL query and return a simplified result.

    Returns:
        {
          "status": "success" | "error",
          "result_type": "vector" | "scalar" | ...,
          "results": [{"metric": {...labels}, "value": <float>}, ...],
          "error": <str, only if status == "error">
        }
    """
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
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
    for item in data.get("result", []):
        # instant vector: item = {"metric": {...}, "value": [ts, "value_str"]}
        _, value_str = item["value"]
        results.append({"metric": item["metric"], "value": float(value_str)})

    return {
        "status": "success",
        "result_type": data.get("resultType"),
        "results": results,
    }