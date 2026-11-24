"""WhatsApp platform searcher — WhatsApp has NO discovery API of any kind (the
WhatsApp Business API is for sending/receiving messages with consenting
contacts, not searching for public contact links). The only honest, authorized
mechanism available is finding `wa.me/<number>` links that happen to already be
publicly indexed by Google on a business's own website/social bio — this
genuinely finds real results only when a business has published its own wa.me
link publicly, which is common for small businesses but rare for individuals.
This is best-effort by design, not a gap to be "fixed" — there is no API to call."""
from __future__ import annotations

import re

import httpx

from app.platforms import web_search
from app.platforms.base import PlatformSearcher, RawCandidate
from app.platforms.site_search import site_restricted_search

_PROFILE_PATTERN = re.compile(r"wa\.me/\d+")


class WhatsAppSearcher(PlatformSearcher):
    name = "WhatsApp"

    def is_configured(self) -> bool:
        return web_search.is_configured()

    def missing_config_error(self) -> str:
        return "Not configured: BRAVE_API_KEY is required (WhatsApp has no discovery API at all — this is best-effort indexed-link discovery only)"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        return await site_restricted_search(client, self.name, "wa.me", raw_query, _PROFILE_PATTERN)
