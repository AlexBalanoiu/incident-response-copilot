from prometheus_tool import query_prometheus


def test_up_query_returns_success():
    result = query_prometheus("up")
    assert result["status"] == "success"
    assert result["result_type"] == "vector"
    assert len(result["results"]) > 0
    # every target should report 1 (up) or 0 (down), nothing else
    for r in result["results"]:
        assert r["value"] in (0.0, 1.0)


def test_bad_query_returns_error():
    result = query_prometheus("this is not promql {{{")
    assert result["status"] == "error"
    assert "error" in result


def test_query_with_no_results():
    result = query_prometheus('up{job="nonexistent-job-xyz"}')
    assert result["status"] == "success"
    assert result["results"] == []