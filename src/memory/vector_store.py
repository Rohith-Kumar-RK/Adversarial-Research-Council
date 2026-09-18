"""
Qdrant wrapper for raw evidence storage.
Runs embedded (on-disk, no server) by default so the project is runnable
with zero infra. Point QDRANT_URL at a real server for production use.
"""
import uuid
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config import QDRANT_URL, QDRANT_API_KEY

COLLECTION = "evidence"
VECTOR_SIZE = 384  # matches the toy hash-embedding below; swap in a real embedder for production


def _get_client() -> QdrantClient:
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(path="./data/qdrant")  # embedded, on-disk


def _ensure_collection(client: QdrantClient):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def _toy_embed(text: str) -> list[float]:
    """
    Deterministic hash-based embedding so the project runs with zero extra
    dependencies/API calls. Swap for a real embedding model (e.g. voyage,
    OpenAI, or a local sentence-transformers model) for real semantic search.
    """
    h = hashlib.sha256(text.encode()).digest()
    vec = [(h[i % len(h)] / 255.0) - 0.5 for i in range(VECTOR_SIZE)]
    return vec


def store_evidence(text: str, source_url: str, topic: str, timestamp: str) -> str:
    client = _get_client()
    _ensure_collection(client)
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=_toy_embed(text),
                payload={"text": text, "source_url": source_url, "topic": topic, "timestamp": timestamp},
            )
        ],
    )
    return point_id


def query_evidence(query: str, topic: str | None = None, limit: int = 8) -> list[dict]:
    client = _get_client()
    _ensure_collection(client)
    query_filter = None
    if topic:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        query_filter = Filter(must=[FieldCondition(key="topic", match=MatchValue(value=topic))])
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=_toy_embed(query),
        query_filter=query_filter,
        limit=limit,
    )
    return [h.payload for h in hits]
