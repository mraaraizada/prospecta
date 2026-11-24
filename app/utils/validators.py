"""Query validation, independent of FastAPI/pydantic — callable and testable on
its own, same pattern as NEXORA/Vortiq's validation layer."""
from __future__ import annotations

MAX_QUERY_LENGTH = 300


def validate_query(query: str) -> str:
    stripped = query.strip()
    if not stripped:
        raise ValueError("query must not be empty")
    if len(stripped) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must be at most {MAX_QUERY_LENGTH} characters, got {len(stripped)}")
    return stripped
