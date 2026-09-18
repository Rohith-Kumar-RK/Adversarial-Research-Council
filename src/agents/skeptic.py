"""
Skeptic: the core differentiator. Actively searches for counter-evidence
and weak sourcing for each Analyst claim, rather than just reviewing tone.
"""
import json
from src.config import LLM_CALL, MAX_DEBATE_ROUNDS
from src.tools.search_tool import web_search

SYSTEM = """You are a skeptical financial analyst whose sole job is to find flaws in claims.
For each claim given, search for reasons it might be wrong: contradicting data, outdated
sources, cherry-picked timeframes, correlation mistaken for causation, or insufficient evidence.
Be specific — cite what you found, not vague doubt. If a claim is actually well-supported,
say so explicitly rather than manufacturing a fake objection.

Respond ONLY with a JSON array: [{"claim": "...", "challenge": "...", "verdict": "survives"|"weakened"|"fails"}]
No prose, no markdown fences."""


def run_skeptic(state: dict) -> dict:
    claims = state["claims"]
    round_num = state.get("debate_round", 0) + 1

    # Give the skeptic real ammunition, not just an opinion — one search per claim, capped.
    counter_evidence = []
    for c in claims[:5]:
        results = web_search(f"{c['claim']} counter evidence OR contradicts", max_results=2)
        counter_evidence.append({"claim": c["claim"], "found": results})

    user_parts = []
    for ce in counter_evidence:
        snippets = "\n".join(f"  - {r['url']}: {r['content'][:200]}" for r in ce["found"])
        user_parts.append(f"Claim: {ce['claim']}\nCounter-search results:\n{snippets}")
    user = "\n\n".join(user_parts)

    raw = LLM_CALL(SYSTEM, user)
    try:
        verdicts = json.loads(raw)
    except json.JSONDecodeError:
        verdicts = [{"claim": c["claim"], "challenge": raw.strip(), "verdict": "weakened"} for c in claims]

    # Only claims that "fail" or are "weakened" go back to Analyst for revision
    challenges = [v for v in verdicts if v.get("verdict") != "survives"]

    state["debate_round"] = round_num
    state["verdicts"] = verdicts
    state["challenges"] = challenges if round_num < MAX_DEBATE_ROUNDS else []
    state["trace"] = state.get("trace", []) + [
        {
            "agent": "Skeptic",
            "action": f"Round {round_num}: {len(challenges)} claims challenged, {len(verdicts) - len(challenges)} survive",
            "detail": verdicts,
        }
    ]
    return state


def should_continue_debate(state: dict) -> str:
    """Routing function for LangGraph conditional edge."""
    if state.get("challenges") and state.get("debate_round", 0) < MAX_DEBATE_ROUNDS:
        return "analyst"
    return "memory_keeper"
