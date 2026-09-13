import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "investigator"))
from embeddings import GeminiEmbeddingFunction
import chromadb

BASE_DIR = Path(__file__).parent.parent.parent
HISTORY_FILE = BASE_DIR / "knowledge_base" / "incident_history" / "incidents.jsonl"
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"
COLLECTION_NAME = "incident_knowledge"


def _next_incident_id() -> str:
    existing_ids = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            for line in f:
                if line.strip():
                    existing_ids.append(json.loads(line)["incident_id"])
    nums = [int(i.split("-")[1]) for i in existing_ids if i.startswith("inc-")]
    next_num = (max(nums) + 1) if nums else 1
    return f"inc-{next_num:04d}"


def append_incident_record(
    scenario: str,
    service: str,
    timestamp: str,
    symptoms_observed: str,
    root_cause: str,
    fix_applied: str,
    resolution_time_minutes: int,
) -> dict:
    """
    Append a resolved incident to the JSONL history AND add it to the live
    vector store, so the next Investigator run can retrieve it immediately -
    this is the Adaptive Memory write-back (feature 2.2).
    """
    record = {
        "incident_id": _next_incident_id(),
        "scenario": scenario,
        "service": service,
        "timestamp": timestamp,
        "symptoms_observed": symptoms_observed,
        "root_cause": root_cause,
        "fix_applied": fix_applied,
        "resolution_time_minutes": resolution_time_minutes,
    }

    needs_leading_newline = (
        HISTORY_FILE.exists()
        and HISTORY_FILE.stat().st_size > 0
        and not HISTORY_FILE.read_bytes().endswith(b"\n")
    )
    with open(HISTORY_FILE, "a") as f:
        if needs_leading_newline:
            f.write("\n")
        f.write(json.dumps(record) + "\n")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=GeminiEmbeddingFunction())
    collection.add(
        ids=[f"incident-{record['incident_id']}"],
        documents=[
            f"Symptoms: {symptoms_observed} Root cause: {root_cause} Fix: {fix_applied}"
        ],
        metadatas=[{
            "source_type": "incident",
            "scenario": scenario,
            "service": service,
            "incident_id": record["incident_id"],
        }],
    )

    return record