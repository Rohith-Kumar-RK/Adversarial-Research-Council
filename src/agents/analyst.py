"""
Analyst: turns raw evidence into discrete, falsifiable claims.
On revision rounds, incorporates the Skeptic's challenge.
"""
import json
from src.config import LLM_CALL

SYSTEM = """You are a financial analyst. Given research evidence, produce a short list of
discrete, falsifiable claims (not vague statements). Each claim must be checkable against
evidence — a specific number, direction, or comparison, not a generality.

Respond ONLY with a JSON array of objects: [{"claim": "...", "basis": "..."}]
No prose, no markdown fences."""

REVISE_SYSTEM = """You are a financial analyst revising claims after a skeptic's challenge.
For each challenged claim, either: (a) strengthen it with better justification, (b) narrow its
scope to what's actually defensible, or (c) drop it if the challenge is fatal.

Respond ONLY with a JSON array of objects: [{"claim": "...", "basis": "..."}]
No prose, no markdown fences."""


def run_analyst(state: dict) -> dict:
    is_revision = bool(state.get("challenges"))

    if not is_revision:
        evidence_text = "\n\n".join(f"[{e['url']}]\n{e['content']}" for e in state["evidence"])
        user = f"Topic: {state['topic']}\n\nEvidence:\n{evidence_text}"
        raw = LLM_CALL(SYSTEM, user)
    else:
        challenges_text = "\n".join(
            f"- Claim: {c['claim']}\n  Challenge: {c['challenge']}" for c in state["challenges"]
        )
        user = f"Topic: {state['topic']}\n\nChallenged claims:\n{challenges_text}"
        raw = LLM_CALL(REVISE_SYSTEM, user)

    try:
        claims = json.loads(raw)
    except json.JSONDecodeError:
        claims = [{"claim": raw.strip(), "basis": "unparsed"}]

    state["claims"] = claims
    state["trace"] = state.get("trace", []) + [
        {"agent": "Analyst", "action": f"{'Revised' if is_revision else 'Produced'} {len(claims)} claims", "detail": claims}
    ]
    return state
