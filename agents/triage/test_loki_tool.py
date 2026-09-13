from loki_tool import query_loki


def test_query_returns_success_shape():
    # promtail ships kubelet/container logs by default, so this should
    # always find *something* across all pods in the last 15 min
    result = query_loki('{namespace="monitoring"}', minutes_back=15)
    assert result["status"] == "success"
    assert isinstance(result["results"], list)


def test_bad_query_returns_error():
    result = query_loki("{{{ not valid logql")
    assert result["status"] == "error"
    assert "error" in result


def test_query_with_no_matches():
    result = query_loki('{namespace="nonexistent-namespace-xyz"}', minutes_back=15)
    assert result["status"] == "success"
    assert result["results"] == []