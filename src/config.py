"""
Central config + the single function every agent uses to call the LLM.

Swap models by editing LLM_CALL only —
nothing in agents/ or graph.py needs to change.
"""

import os

from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()


# =========================
# API KEYS
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# =========================
# DATABASE CONFIGURATION
# =========================

QDRANT_URL = os.getenv("QDRANT_URL") or None
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687"
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j"
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
    "research_council_pw"
)


# =========================
# AGENT CONFIGURATION
# =========================

MAX_DEBATE_ROUNDS = int(
    os.getenv("MAX_DEBATE_ROUNDS", "3")
)


# =========================
# GEMINI MODEL
# =========================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


# =========================
# GEMINI CLIENT
# =========================

_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# =========================
# SHARED LLM FUNCTION
# =========================

def LLM_CALL(
    system: str,
    user: str,
    max_tokens: int = 1500
) -> str:
    """
    One shared entry point for every agent's LLM calls.

    All agents should call this function instead of
    directly calling the Gemini API.
    """

    if _client is None:
        raise RuntimeError(
            "GEMINI_API_KEY not set — "
            "copy .env.example to .env and add your Gemini API key."
        )

    prompt = f"""
System instructions:
{system}

User request:
{user}
"""

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "max_output_tokens": max_tokens,
        },
    )

    if response.text:
        return response.text

    return ""
