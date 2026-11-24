"""YouTube platform searcher — the one platform in this project with a real,
direct, authorized keyword-search API (not routed through Google Custom Search).
Official docs: https://developers.google.com/youtube/v3/docs/search/list
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.platforms.base import PlatformSearcher, PlatformSearchError, RawCandidate

_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"


class YouTubeSearcher(PlatformSearcher):
    name = "YouTube"

    def is_configured(self) -> bool:
        return bool(settings.youtube_api_key)

    def missing_config_error(self) -> str:
        return "Not configured: YOUTUBE_API_KEY is required"

    async def search(self, client: httpx.AsyncClient, query_intent: dict, raw_query: str) -> list[RawCandidate]:
        params = {
            "key": settings.youtube_api_key,
            "part": "snippet",
            "type": "channel",
            "q": raw_query,
            "maxResults": settings.max_results_per_platform,
        }
        try:
            resp = await client.get(_ENDPOINT, params=params, timeout=settings.request_timeout_seconds)
        except httpx.TimeoutException as exc:
            raise PlatformSearchError("YouTube API request timed out") from exc
        except httpx.HTTPError as exc:
            raise PlatformSearchError(f"YouTube API request failed: {exc}") from exc

        if resp.status_code != 200:
            try:
                detail = resp.json().get("error", {}).get("message", resp.text[:200])
            except ValueError:
                detail = resp.text[:200]
            raise PlatformSearchError(f"YouTube API error (HTTP {resp.status_code}): {detail}")

        body = resp.json()
        candidates = []
        for item in body.get("items", []):
            snippet = item.get("snippet", {})
            channel_id = item.get("id", {}).get("channelId")
            if not channel_id:
                continue
            candidates.append(
                RawCandidate(
                    platform=self.name,
                    title=snippet.get("title", ""),
                    snippet=snippet.get("description", ""),
                    link=f"https://www.youtube.com/channel/{channel_id}",
                )
            )
        return candidates
