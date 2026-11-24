"""Orchestrates the full pipeline: validate -> parse intent (LLM) -> fan out
across platforms concurrently -> relevance-filter (LLM, one batched call) ->
extract contact info -> consolidate duplicates -> structured response.

Mirrors NEXORA/Vortiq's isolation pattern: one platform's search failure never
prevents the others from being attempted, and any stage's failure degrades to a
clean ProspectDiscoveryResponse(success=False, error=...) rather than a 500.
"""
from __future__ import annotations

import asyncio

import httpx

from app.config import settings
from app.platforms.base import PlatformSearcher, PlatformSearchError, RawCandidate
from app.platforms.facebook import FacebookSearcher
from app.platforms.google import GoogleSearcher
from app.platforms.instagram import InstagramSearcher
from app.platforms.linkedin import LinkedInSearcher
from app.platforms.threads import ThreadsSearcher
from app.platforms.whatsapp import WhatsAppSearcher
from app.platforms.x_platform import XSearcher
from app.platforms.youtube import YouTubeSearcher
from app.schemas import ProspectDiscoveryResponse
from app.services.deduplication_service import consolidate
from app.services.llm_service import LLMServiceError, parse_query_intent
from app.services.profile_extractor import extract_profile
from app.services.query_service import build_search_terms
from app.services.relevance_service import filter_relevant
from app.utils.validators import validate_query

#: The platform registry — the single place platform selection is decided.
PLATFORM_SEARCHERS: list[PlatformSearcher] = [
    GoogleSearcher(),
    LinkedInSearcher(),
    XSearcher(),
    YouTubeSearcher(),
    InstagramSearcher(),
    FacebookSearcher(),
    ThreadsSearcher(),
    WhatsAppSearcher(),
]


def _location_label(intent: dict) -> str | None:
    location = intent.get("location") or {}
    parts = [location.get("city"), location.get("state"), location.get("country")]
    joined = ", ".join(p for p in parts if p)
    return joined or None


async def _search_one(searcher: PlatformSearcher, client: httpx.AsyncClient, intent: dict, search_terms: str) -> list[RawCandidate]:
    if not searcher.is_configured():
        return []
    try:
        return await searcher.search(client, intent, search_terms)
    except PlatformSearchError:
        # One platform's real failure (API error, timeout, not configured) never
        # prevents the others from being attempted — isolated the same way
        # NEXORA isolates one posting platform's failure from the rest.
        return []
    except Exception:  # noqa: BLE001 - last-resort isolation, same as NEXORA.
        return []


async def discover_prospects(query: str) -> ProspectDiscoveryResponse:
    try:
        validate_query(query)
    except ValueError as exc:
        return ProspectDiscoveryResponse(success=False, query=query, total_prospects=0, error=str(exc))

    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            intent = await parse_query_intent(client, query)
        except LLMServiceError as exc:
            return ProspectDiscoveryResponse(success=False, query=query, total_prospects=0, error=str(exc))

        search_terms = build_search_terms(intent)
        results = await asyncio.gather(*(_search_one(s, client, intent, search_terms) for s in PLATFORM_SEARCHERS))
        all_candidates: list[RawCandidate] = [c for platform_results in results for c in platform_results]

        try:
            relevant = await filter_relevant(client, intent, all_candidates)
        except LLMServiceError as exc:
            return ProspectDiscoveryResponse(success=False, query=query, total_prospects=0, error=str(exc))

    hits = [extract_profile(item) for item in relevant]
    prospects = consolidate(hits, _location_label(intent))

    return ProspectDiscoveryResponse(success=True, query=query, total_prospects=len(prospects), prospects=prospects)
