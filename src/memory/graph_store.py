"""
Neo4j wrapper. This is where cross-session contradiction detection lives —
the differentiator vs. a stateless research pipeline.

Graph shape:
  (:Entity {name})-[:HAS_CLAIM]->(:Claim {text, confidence, session_id, timestamp, stance})
"""
from datetime import datetime
from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def close():
    if _driver is not None:
        _driver.close()


def log_claim(entity: str, claim_text: str, confidence: float, session_id: str, stance: str = "affirmed"):
    """stance: 'affirmed' | 'contradicted' | 'unresolved'"""
    query = """
    MERGE (e:Entity {name: $entity})
    CREATE (c:Claim {
        text: $claim_text,
        confidence: $confidence,
        session_id: $session_id,
        timestamp: $timestamp,
        stance: $stance
    })
    MERGE (e)-[:HAS_CLAIM]->(c)
    """
    with _get_driver().session() as session:
        session.run(
            query,
            entity=entity,
            claim_text=claim_text,
            confidence=confidence,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            stance=stance,
        )


def find_prior_claims(entity: str, exclude_session: str, limit: int = 10) -> list[dict]:
    """Pull past claims about this entity from earlier sessions, for contradiction checking."""
    query = """
    MATCH (e:Entity {name: $entity})-[:HAS_CLAIM]->(c:Claim)
    WHERE c.session_id <> $exclude_session
    RETURN c.text AS text, c.confidence AS confidence, c.timestamp AS timestamp, c.stance AS stance
    ORDER BY c.timestamp DESC
    LIMIT $limit
    """
    with _get_driver().session() as session:
        result = session.run(query, entity=entity, exclude_session=exclude_session, limit=limit)
        return [dict(r) for r in result]
