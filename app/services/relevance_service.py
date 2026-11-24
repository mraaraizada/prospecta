"""Wraps the LLM's batched relevance scoring, mapping results back to candidates
by their assigned id — the ONE place an LLM judgment call is converted into a
filtering decision."""
from __future__ import annotations

import httpx

from app.platforms.base import RawCandidate
from app.services.llm_service import score_relevance_batch


async def filter_relevant(client: httpx.AsyncClient, intent: dict, candidates: list[RawCandidate]) -> list[dict]:
    """Returns a list of {"candidate": RawCandidate, "display_name": str, "reason": str}
    for every candidate the LLM judged genuinely relevant — never includes a
    candidate the LLM marked is_relevant=false, and never invents a name the LLM
    didn't itself extract from the real title/snippet."""
    if not candidates:
        return []

    indexed = [{"id": i, "platform": c["platform"], "title": c["title"], "snippet": c["snippet"]} for i, c in enumerate(candidates)]
    judgments = await score_relevance_batch(client, intent, indexed)
    judgments_by_id = {j["id"]: j for j in judgments if "id" in j}

    kept = []
    for i, candidate in enumerate(candidates):
        judgment = judgments_by_id.get(i)
        if judgment and judgment.get("is_relevant") and judgment.get("display_name"):
            kept.append({"candidate": candidate, "display_name": judgment["display_name"], "reason": judgment.get("reason", "")})
    return kept
