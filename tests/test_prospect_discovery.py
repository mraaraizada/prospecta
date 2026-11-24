"""Orchestration tests: full pipeline (mocked LLM + mocked platform searches),
plus the real FastAPI route's validation responses."""
from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.prospect_service import discover_prospects

GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
YOUTUBE_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"

_INTENT_BODY = {"interest": "Football", "audience": "Football lovers", "location": {"city": "Washington DC", "state": "DC", "country": "USA"}, "target_type": "individual"}
_RELEVANCE_BODY = {"results": [{"id": 0, "is_relevant": True, "display_name": "John Smith", "reason": "Matches football and DC"}]}


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "brave_api_key", "test-key")
    monkeypatch.setattr(settings, "youtube_api_key", "test-yt-key")


def _mock_gemini_calls():
    call_count = {"n": 0}

    def responder(request):
        call_count["n"] += 1
        body = _INTENT_BODY if call_count["n"] == 1 else _RELEVANCE_BODY
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]})

    respx.post(GEMINI_ENDPOINT).mock(side_effect=responder)


@respx.mock
async def test_full_pipeline_success():
    _mock_gemini_calls()
    respx.get(BRAVE_ENDPOINT).mock(return_value=httpx.Response(200, json={"web": {"results": [{"title": "John Smith - Football Fan", "description": "Lives in DC, loves football", "url": "https://www.linkedin.com/in/johnsmith"}]}}))
    respx.get(YOUTUBE_ENDPOINT).mock(return_value=httpx.Response(200, json={"items": []}))

    response = await discover_prospects("Football lovers in Washington DC in USA")
    assert response.success is True
    assert response.total_prospects == 1
    assert response.prospects[0].name == "John Smith"
    assert response.prospects[0].location == "Washington DC, DC, USA"


@respx.mock
async def test_invalid_query_is_a_clean_failure_not_a_crash():
    response = await discover_prospects("")
    assert response.success is False
    assert response.total_prospects == 0


@respx.mock
async def test_llm_intent_failure_is_a_clean_result():
    respx.post(GEMINI_ENDPOINT).mock(return_value=httpx.Response(429, json={"error": {"message": "Resource exhausted"}}))
    response = await discover_prospects("Football lovers in Washington DC")
    assert response.success is False
    assert "429" in response.error


@respx.mock
async def test_one_platform_failure_does_not_crash_the_whole_request():
    _mock_gemini_calls()
    respx.get(BRAVE_ENDPOINT).mock(return_value=httpx.Response(500))
    respx.get(YOUTUBE_ENDPOINT).mock(return_value=httpx.Response(200, json={"items": [{"id": {"channelId": "UC1"}, "snippet": {"title": "DC Football Channel", "description": "All about DC football"}}]}))

    response = await discover_prospects("Football lovers in Washington DC")
    # Google/LinkedIn/X/Instagram/Facebook/Threads/WhatsApp all use the same
    # (failing) Brave endpoint and are isolated; the request still completes.
    assert response.success is True


@respx.mock
async def test_no_relevant_results_returns_empty_prospect_list_not_a_failure():
    def responder(request):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(_INTENT_BODY)}]}}]})

    call_count = {"n": 0}

    def gemini_responder(request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(_INTENT_BODY)}]}}]})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps({"results": []})}]}}]})

    respx.post(GEMINI_ENDPOINT).mock(side_effect=gemini_responder)
    respx.get(BRAVE_ENDPOINT).mock(return_value=httpx.Response(200, json={"web": {"results": []}}))
    respx.get(YOUTUBE_ENDPOINT).mock(return_value=httpx.Response(200, json={"items": []}))

    response = await discover_prospects("Football lovers in Washington DC")
    assert response.success is True
    assert response.total_prospects == 0
    assert response.prospects == []


# ---------------------------------------------------------------------------
# Real HTTP-level validation tests against the FastAPI route
# ---------------------------------------------------------------------------

client = TestClient(app)


def test_route_rejects_empty_query():
    resp = client.post("/prospect-discovery", json={"query": ""})
    assert resp.status_code == 422


def test_route_rejects_overlong_query():
    resp = client.post("/prospect-discovery", json={"query": "a" * 301})
    assert resp.status_code == 422


def test_docs_endpoint_is_available():
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_schema_is_available():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "Prospecta — AI-Powered Multi-Platform Prospect Discovery"
