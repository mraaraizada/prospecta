"""Google platform searcher — the spec explicitly treats Google as a discovery
source whose results get resolved into real individual/business profiles (not
generic search-result URLs), so this module's results feed the relevance/
consolidation pipeline the same as every other platform rather than being
returned as raw Google links."""
from __future__ import annotations

import httpx

from app.platforms import search_provider
from app.platforms.base import PlatformSearcher, PlatformSearchError, RawCandidate


class GoogleSearcher(PlatformSearcher):
    name = "Google"

    def is_configured(self) -> bool:
        return search_provider.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: SERPER_API_KEY is required"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        try:
            results = await search_provider.search(client, raw_query)
        except search_provider.SearchProviderError as exc:
            raise PlatformSearchError(str(exc)) from exc
        return [RawCandidate(platform=self.name, title=r["title"], snippet=r["snippet"], link=r["link"]) for r in results]
