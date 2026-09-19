# Adversarial Research Council

Multi-agent market/finance research system. Five agents, one debate loop, self-checking by design.

## Why this is different

Most agentic research demos are a straight pipeline: `search → summarize → write`. That produces
confident-sounding output built on whatever the first search happened to return. This project adds
an adversarial step: a **Skeptic** agent whose only job is to attack the Analyst's claims before
anything gets published. Claims that survive get a confidence score. Claims that don't survive get
revised or dropped. A **Memory Keeper** also checks new findings against past research sessions and
flags contradictions across time — e.g. "last month's data said margin was expanding; today's says
it's contracting — worth a second look."

## Methodology

1. **Scout** — pulls raw data (news, filings, market data) via web search tools. Stores raw
   evidence in vector memory (Qdrant), tagged with source + timestamp.
2. **Analyst** — reads the evidence, produces a set of discrete, falsifiable claims
   (e.g. "Company X revenue grew >10% YoY in Q2").
3. **Skeptic** — for each claim, actively searches for contradicting evidence or weak sourcing.
   Produces a challenge. Analyst gets one revision pass. This repeats up to `MAX_DEBATE_ROUNDS`
   (default 3) per claim.
4. **Synthesizer** — reconciles surviving claims + unresolved disagreements into a final report,
   each claim tagged with a confidence score (0-1) derived from how the debate went.
5. **Memory Keeper** — writes the session's claims to Neo4j as nodes, linked by topic/entity.
   Before Synthesizer finalizes, Memory Keeper queries the graph for prior claims about the same
   entity and flags contradictions for the report.

## Architecture

```
                    ┌─────────┐
                    │  Scout  │  (web search → Qdrant)
                    └────┬────┘
                         ▼
                    ┌─────────┐
              ┌────▶│ Analyst │
              │     └────┬────┘
              │          ▼
              │     ┌─────────┐
              │     │ Skeptic │  (challenge, up to N rounds)
              │     └────┬────┘
              │          │ revise? ──yes──┘
              │          │ no
              │          ▼
              │  ┌───────────────┐
              │  │ Memory Keeper │  (Neo4j: log + contradiction check)
              │  └───────┬───────┘
              │          ▼
              │  ┌───────────────┐
              └──│ Synthesizer   │  (final report + confidence)
                 └───────────────┘
```

Built with **LangGraph** because the debate loop is a cyclic graph (Analyst ↔ Skeptic), not a
linear chain — this is the actual reason to reach for LangGraph over CrewAI here.

## Stack

- Orchestration: LangGraph
- LLM: Google AI Studio API (Gemini)
- Search: Tavily API
- Vector memory: Qdrant (local/embedded mode by default, no server needed to try it)
- Graph memory: Neo4j (needs a running instance — see docker-compose.yml)
- UI: Streamlit (shows the debate trace live, not just the final answer)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY and TAVILY_API_KEY
docker compose up -d   # starts Neo4j (Qdrant runs embedded, no container needed)
python src/main.py "Is Nvidia's data center margin expansion sustainable?"
# or, for the live dashboard:
streamlit run app.py
```

## Files

- `src/agents/` — one file per role, each a plain function `(state) -> state`
- `src/graph.py` — LangGraph wiring, the debate loop, routing logic
- `src/memory/vector_store.py` — Qdrant wrapper
- `src/memory/graph_store.py` — Neo4j wrapper + contradiction query
- `src/tools/search_tool.py` — Tavily wrapper
- `src/main.py` — CLI entry point
- `app.py` — Streamlit dashboard, streams each agent's turn as it happens

## Extending

- Swap Tavily for SerpAPI/Playwright scraping in `tools/search_tool.py` — nothing else changes.
- Add a "Devil's Advocate" second Skeptic with a different persona/temperature for more diverse
  challenges — just add another conditional node in `graph.py`.
- Swap any LLM for a local model (Ollama) by changing `src/config.py` `LLM_CALL` function only.
