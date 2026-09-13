# agents/investigator/ingest.py
import json
import re
from pathlib import Path

import chromadb
from embeddings import GeminiEmbeddingFunction

BASE_DIR = Path(__file__).parent.parent.parent
RUNBOOK_DIR = BASE_DIR / "knowledge_base" / "runbooks"
HISTORY_FILE = BASE_DIR / "knowledge_base" / "incident_history" / "incidents.jsonl"
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"

COLLECTION_NAME = "incident_knowledge"


def _parse_runbook(path: Path) -> dict:
    text = path.read_text()
    fm_match = re.match(r"^---\nscenario: (\w+)\nservice_type: (\w+)\n---\n\n(.*)", text, re.DOTALL)
    scenario, service_type, body = fm_match.groups()
    return {"scenario": scenario, "service_type": service_type, "body": body.strip()}


def build_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    client.delete_collection(COLLECTION_NAME) if COLLECTION_NAME in [c.name for c in client.list_collections()] else None
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=GeminiEmbeddingFunction(),
    )

    ids, documents, metadatas = [], [], []

    for path in RUNBOOK_DIR.glob("*.md"):
        rb = _parse_runbook(path)
        ids.append(f"runbook-{rb['scenario']}")
        documents.append(rb["body"])
        metadatas.append({
            "source_type": "runbook",
            "scenario": rb["scenario"],
            "service_type": rb["service_type"],
        })

    with open(HISTORY_FILE) as f:
        for line in f:
            if not line.strip():
                continue
            inc = json.loads(line)
            ids.append(f"incident-{inc['incident_id']}")
            documents.append(
                f"Symptoms: {inc['symptoms_observed']} "
                f"Root cause: {inc['root_cause']} "
                f"Fix: {inc['fix_applied']}"
            )
            metadatas.append({
                "source_type": "incident",
                "scenario": inc["scenario"],
                "service": inc["service"],
                "incident_id": inc["incident_id"],
            })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return collection


if __name__ == "__main__":
    collection = build_collection()
    print(f"Ingested {collection.count()} documents into '{COLLECTION_NAME}'.")