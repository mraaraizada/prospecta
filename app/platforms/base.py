"""Common interface every platform searcher implements — mirrors the adapter
pattern used in NEXORA/Vortiq: each platform owns its own query construction and
result shaping; the orchestrator never touches a platform's search mechanics
directly (see services/prospect_service.py)."""
from __future__ import annotations

from abc import ABC, abstractmethod

import httpx


class RawCandidate(dict):
    """platform: str, title: str, snippet: str, link: str — fields taken verbatim
    from a real search result, never invented."""


class PlatformSearcher(ABC):
    #: Platform name used in the response's "platform" field — must match the
    #: spec's defined platform names exactly.
    name: str

    def is_configured(self) -> bool:
        return True

    def missing_config_error(self) -> str:
        return "Not configured"

    @abstractmethod
    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        """Returns real candidates found for this platform, or raises
        PlatformSearchError on a genuine failure. An empty list (no error) means
        the search succeeded but found nothing relevant-shaped."""
        raise NotImplementedError


class PlatformSearchError(Exception):
    """Raised by a platform's search() for a real, specific failure."""
