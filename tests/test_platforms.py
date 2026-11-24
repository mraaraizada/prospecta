"""Platform searcher tests. All HTTP mocked with respx — no real network calls."""
from __future__ import annotations

import httpx
import pytest
import respx

from app.config import settings
from app.platforms.base import PlatformSearchError
from app.platforms.facebook import FacebookSearcher
from app.platforms.google import GoogleSearcher
from app.platforms.instagram import InstagramSearcher
from app.platforms.linkedin import LinkedInSearcher
from app.platforms.threads import ThreadsSearcher
from app.platforms.whatsapp import WhatsAppSearcher
from app.platforms.x_platform import XSearcher
from app.platforms.youtube import YouTubeSearcher

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
YOUTUBE_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
INTENT = {"interest": "Football", "audience": "Football lovers", "location": {"city": "Washington DC"}, "target_type": "individual"}


def _brave_response(results: list[dict]) -> httpx.Response:
    return httpx.Response(200, json={"web": {"results": results}})


@pytest.fixture
def client():
    return httpx.AsyncClient()


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "brave_api_key", "test-key")
    monkeypatch.setattr(settings, "youtube_api_key", "test-yt-key")


@respx.mock
async def test_google_searcher_returns_real_result_fields(client):
    respx.get(BRAVE_ENDPOINT).mock(
        return_value=_brave_response([{"title": "John Smith - Football Fan", "description": "Loves football in DC", "url": "https://example.com/john"}])
    )
    results = await GoogleSearcher().search(client, INTENT, "Football lovers Washington DC")
    assert results[0]["platform"] == "Google"
    assert results[0]["title"] == "John Smith - Football Fan"
    assert results[0]["link"] == "https://example.com/john"


@respx.mock
async def test_google_searcher_not_configured_raises(client, monkeypatch):
    monkeypatch.setattr(settings, "brave_api_key", None)
    with pytest.raises(PlatformSearchError, match="Not configured"):
        await GoogleSearcher().search(client, INTENT, "query")


@respx.mock
async def test_linkedin_searcher_filters_to_real_profile_urls(client):
    respx.get(BRAVE_ENDPOINT).mock(
        return_value=_brave_response(
            [
                {"title": "John Smith", "description": "Football fan in DC", "url": "https://www.linkedin.com/in/johnsmith"},
                {"title": "LinkedIn Help Center", "description": "General help", "url": "https://www.linkedin.com/help/linkedin/answer/123"},
            ]
        )
    )
    results = await LinkedInSearcher().search(client, INTENT, "Football lovers Washington DC")
    assert len(results) == 1
    assert results[0]["link"] == "https://www.linkedin.com/in/johnsmith"


@respx.mock
async def test_x_searcher_filters_out_status_urls(client):
    respx.get(BRAVE_ENDPOINT).mock(
        return_value=_brave_response(
            [
                {"title": "John Smith (@johnsmith)", "description": "Football fan", "url": "https://x.com/johnsmith"},
                {"title": "A post", "description": "...", "url": "https://x.com/johnsmith/status/12345"},
            ]
        )
    )
    results = await XSearcher().search(client, INTENT, "Football lovers")
    assert len(results) == 1
    assert results[0]["link"] == "https://x.com/johnsmith"


@respx.mock
async def test_instagram_searcher_filters_out_post_urls(client):
    respx.get(BRAVE_ENDPOINT).mock(
        return_value=_brave_response(
            [
                {"title": "John Smith", "description": "Football lover", "url": "https://www.instagram.com/johnsmith"},
                {"title": "A post", "description": "...", "url": "https://www.instagram.com/p/Cabc123/"},
            ]
        )
    )
    results = await InstagramSearcher().search(client, INTENT, "Football lovers")
    assert len(results) == 1
    assert "johnsmith" in results[0]["link"]


@respx.mock
async def test_facebook_searcher_filters_out_policy_pages(client):
    respx.get(BRAVE_ENDPOINT).mock(
        return_value=_brave_response(
            [
                {"title": "John Smith", "description": "Football fan", "url": "https://www.facebook.com/johnsmith"},
                {"title": "Terms", "description": "...", "url": "https://www.facebook.com/terms/"},
            ]
        )
    )
    results = await FacebookSearcher().search(client, INTENT, "Football lovers")
    assert len(results) == 1


@respx.mock
async def test_threads_searcher_filters_to_handle_urls(client):
    respx.get(BRAVE_ENDPOINT).mock(return_value=_brave_response([{"title": "John Smith", "description": "Football", "url": "https://www.threads.net/@johnsmith"}]))
    results = await ThreadsSearcher().search(client, INTENT, "Football lovers")
    assert len(results) == 1


@respx.mock
async def test_whatsapp_searcher_finds_real_wa_me_links(client):
    respx.get(BRAVE_ENDPOINT).mock(return_value=_brave_response([{"title": "Contact us", "description": "WhatsApp", "url": "https://wa.me/12025550147"}]))
    results = await WhatsAppSearcher().search(client, INTENT, "football shop")
    assert len(results) == 1


@respx.mock
async def test_youtube_searcher_returns_real_channel_urls(client):
    respx.get(YOUTUBE_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"id": {"channelId": "UC12345"}, "snippet": {"title": "DC Football Fan Channel", "description": "All about football in DC"}}]},
        )
    )
    results = await YouTubeSearcher().search(client, INTENT, "Football lovers Washington DC")
    assert results[0]["link"] == "https://www.youtube.com/channel/UC12345"
    assert results[0]["platform"] == "YouTube"


@respx.mock
async def test_youtube_searcher_api_error_is_a_real_failure(client):
    respx.get(YOUTUBE_ENDPOINT).mock(return_value=httpx.Response(403, json={"error": {"message": "quota exceeded"}}))
    with pytest.raises(PlatformSearchError, match="quota exceeded"):
        await YouTubeSearcher().search(client, INTENT, "query")


async def test_youtube_searcher_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "youtube_api_key", None)
    assert YouTubeSearcher().is_configured() is False
