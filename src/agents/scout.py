"""
Scout: pulls raw evidence, stores it in Qdrant tagged by topic.
Does NOT interpret — that's the Analyst's job. Scout stays close to source.
"""
from datetime import datetime
from src.tools.search_tool import web_search
from src.memory.vector_store import store_evidence


def run_scout(state: dict) -> dict:
    topic = state["topic"]
    results = web_search(topic, max_results=6)

    evidence = []
    for r in results:
        store_evidence(
            text=r["content"],
            source_url=r["url"],
            topic=topic,
            timestamp=datetime.utcnow().isoformat(),
        )
        evidence.append(r)

    state["evidence"] = evidence
    state["trace"] = state.get("trace", []) + [
        {"agent": "Scout", "action": f"Gathered {len(evidence)} sources", "detail": [e["url"] for e in evidence]}
    ]
    return state
