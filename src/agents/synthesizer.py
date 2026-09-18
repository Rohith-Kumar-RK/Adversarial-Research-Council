"""
Synthesizer: produces the final report. Every claim carries a confidence
score derived from the debate outcome, and any cross-session contradictions
are surfaced explicitly rather than silently dropped.
"""
from src.config import LLM_CALL

SYSTEM = """You are writing the final section of a financial research report. You are given:
- surviving claims with confidence verdicts from an internal debate process
- any contradictions found against past research on the same entity

Write a concise report (under 400 words). For each claim, state it plainly and note its
confidence level in parentheses. If there are contradictions with past findings, include a
short "Watch List" section flagging them — do not resolve the contradiction yourself, just
surface it clearly so a human can investigate.

Do not editorialize beyond what the evidence supports."""


def run_synthesizer(state: dict) -> dict:
    verdicts = state.get("verdicts", [])
    contradictions = state.get("contradictions", [])

    claims_text = "\n".join(f"- {v['claim']} [{v.get('verdict', 'unresolved')}]" for v in verdicts)
    contradictions_text = (
        "\n".join(f"- Today: {c['today_claim']} vs Past ({c['past_timestamp']}): {c['past_claim']}" for c in contradictions)
        or "None found."
    )

    user = f"Topic: {state['topic']}\n\nClaims:\n{claims_text}\n\nContradictions vs past research:\n{contradictions_text}"
    report = LLM_CALL(SYSTEM, user, max_tokens=800)

    state["report"] = report
    state["trace"] = state.get("trace", []) + [
        {"agent": "Synthesizer", "action": "Produced final report", "detail": report}
    ]
    return state
