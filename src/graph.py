"""
LangGraph wiring. The debate loop (Analyst <-> Skeptic) is a cycle, which is
why this is built on LangGraph's StateGraph rather than a linear chain —
CrewAI/plain function composition can't express "loop until claims stabilize
or round limit hit" as cleanly.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from src.agents.scout import run_scout
from src.agents.analyst import run_analyst
from src.agents.skeptic import run_skeptic, should_continue_debate
from src.agents.memory_keeper import run_memory_keeper
from src.agents.synthesizer import run_synthesizer


class CouncilState(TypedDict, total=False):
    topic: str
    session_id: str
    evidence: list
    claims: list
    challenges: list
    verdicts: list
    debate_round: int
    entity: str
    contradictions: list
    report: str
    trace: list


def build_graph():
    graph = StateGraph(CouncilState)

    graph.add_node("scout", run_scout)
    graph.add_node("analyst", run_analyst)
    graph.add_node("skeptic", run_skeptic)
    graph.add_node("memory_keeper", run_memory_keeper)
    graph.add_node("synthesizer", run_synthesizer)

    graph.set_entry_point("scout")
    graph.add_edge("scout", "analyst")
    graph.add_edge("analyst", "skeptic")

    # The loop: skeptic decides whether claims go back to analyst or move on
    graph.add_conditional_edges(
        "skeptic",
        should_continue_debate,
        {"analyst": "analyst", "memory_keeper": "memory_keeper"},
    )

    graph.add_edge("memory_keeper", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()
