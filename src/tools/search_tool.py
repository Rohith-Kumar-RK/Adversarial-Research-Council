"""
Search wrapper. Swap Tavily for SerpAPI or a Playwright scraper here —
Scout and Skeptic don't need to know which backend is used.
"""
from tavily import TavilyClient

from src.config import TAVILY_API_KEY


_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Tavily maximum query length
MAX_QUERY_LENGTH = 1500


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using Tavily.

    Returns a list of:
    {
        "title": str,
        "url": str,
        "content": str,
        "score": float
    }
    """

    if _client is None:
        raise RuntimeError(
            "TAVILY_API_KEY not set — "
            "copy .env.example to .env and fill it in."
        )

    # Convert to string and remove unnecessary whitespace/newlines
    query = " ".join(str(query).split())

    # Prevent Tavily BadRequestError for oversized queries
    if len(query) > MAX_QUERY_LENGTH:
        print(
            f"[TAVILY] Query too long ({len(query)} characters). "
            f"Truncating to {MAX_QUERY_LENGTH} characters."
        )

        query = query[:MAX_QUERY_LENGTH]

    print(f"[TAVILY] Searching ({len(query)} chars): {query}")

    result = _client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
    )

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in result.get("results", [])
    ]
# Why this fi