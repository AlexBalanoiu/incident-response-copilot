import chromadb
from embeddings import GeminiEmbeddingFunction
from pathlib import Path

CHROMA_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "chroma_db"
COLLECTION_NAME = "incident_knowledge"

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_collection(name=COLLECTION_NAME, embedding_function=GeminiEmbeddingFunction())


def search_knowledge_base(symptom_description: str, n_results: int = 5) -> dict:
    """
    Search runbooks and past incidents for entries matching a symptom description.

    Returns:
        {
          "status": "success",
          "results": [
            {"source_type": "runbook"|"incident", "scenario": <str>,
             "content": <str>, "distance": <float>}, ...
          ]
        }
    """
    results = _collection.query(query_texts=[symptom_description], n_results=n_results)

    entries = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        entries.append({
            "source_type": meta["source_type"],
            "scenario": meta["scenario"],
            "content": doc,
            "distance": dist,
        })

    return {"status": "success", "results": entries}