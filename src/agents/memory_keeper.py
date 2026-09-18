"""
Memory Keeper: logs this session's claims to Neo4j, and checks whether
today's claims contradict what past sessions found about the same entity.
This is what makes the system stateful across research sessions instead
of re-litigating the same question from scratch every time.
"""
import json
from src.config import LLM_CALL
from src.memory import graph_store

EXTRACT_ENTITY_SYSTEM = """Given a research topic, extract the single primary entity being
researched (a company name, ticker, or sector). Respond with just the entity name, nothing else."""

CONTRADICTION_SYSTEM = """Compare today's claims against past claims about the same entity.
Flag any that directly contradict each other (not just different framing — an actual conflict
in direction or magnitude). Respond ONLY with a JSON array:
[{"today_claim": "...", "past_claim": "...", "past_timestamp": "...", "conflict": "description"}]
If no contradictions, respond with []. No prose, no markdown fences."""


def run_memory_keeper(state: dict) -> dict:
    entity = LLM_CALL(EXTRACT_ENTITY_SYSTEM, state["topic"], max_tokens=50).strip()
    session_id = state["session_id"]

    verdicts = state.get("verdicts", [])
    surviving = [v for v in verdicts if v.get("verdict") == "survives"] or verdicts

    for v in surviving:
        confidence = {"survives": 0.85, "weakened": 0.5, "fails": 0.15}.get(v.get("verdict"), 0.5)
        graph_store.log_claim(
            entity=entity,
            claim_text=v["claim"],
            confidence=confidence,
            session_id=session_id,
            stance=v.get("verdict", "unresolved"),
        )

    prior_claims = graph_store.find_prior_claims(entity, exclude_session=session_id)

    contradictions = []
    if prior_claims:
        today_text = "\n".join(f"- {v['claim']}" for v in surviving)
        past_text = "\n".join(f"- [{p['timestamp']}] {p['text']}" for p in prior_claims)
        raw = LLM_CALL(CONTRADICTION_SYSTEM, f"Today's claims:\n{today_text}\n\nPast claims:\n{past_text}")
        try:
            contradictions = json.loads(raw)
        except json.JSONDecodeError:
            contradictions = []

    state["entity"] = entity
    state["contradictions"] = contradictions
    state["trace"] = state.get("trace", []) + [
        {
            "agent": "Memory Keeper",
            "action": f"Logged claims for '{entity}', checked {len(prior_claims)} prior claims, found {len(contradictions)} contradictions",
            "detail": contradictions,
        }
    ]
    print("\n========== MEMORY KEEPER DEBUG ==========")
    print("Topic:", state.get("topic"))
    print("Session ID:", state.get("session_id"))
    print("Verdicts:", state.get("verdicts"))
    print("Number of verdicts:", len(state.get("verdicts", [])))
    return state
