from ingest import build_collection

collection = build_collection()


def _top_scenarios(query: str, n: int = 3) -> list[str]:
    results = collection.query(query_texts=[query], n_results=n)
    return [m["scenario"] for m in results["metadatas"][0]]


def test_connection_leak_query_retrieves_db_connection_exhaustion():
    top = _top_scenarios("app throwing errors about too many open connections to the database")
    assert "db_connection_exhaustion" in top


def test_gradual_memory_growth_query_retrieves_memory_leak():
    top = _top_scenarios("pod memory keeps climbing slowly over hours until it gets killed")
    assert "memory_leak" in top


def test_missing_index_query_retrieves_slow_query():
    top = _top_scenarios("queries are taking much longer than usual but the app server isn't under load")
    assert "slow_query" in top


def test_collection_contains_both_source_types():
    results = collection.query(query_texts=["pod restarted unexpectedly"], n_results=10)
    source_types = {m["source_type"] for m in results["metadatas"][0]}
    assert "runbook" in source_types
    assert "incident" in source_types