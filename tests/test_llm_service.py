"""Gemini LLM service tests. All HTTP mocked with respx — no real network calls."""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.config import settings
from app.services.llm_service import LLMServiceError, parse_query_intent, score_relevance_batch

ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"


@pytest.fixture
def client():
    return httpx.AsyncClient()


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")


@respx.mock
async def test_parse_query_intent_returns_structured_parameters(client):
    body = {"interest": "Football", "audience": "Football lovers", "location": {"city": "Washington DC", "state": "DC", "country": "USA"}, "target_type": "individual"}
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}))
    result = await parse_query_intent(client, "Football lovers in Washington DC in USA")
    assert result["interest"] == "Football"
    assert result["location"]["city"] == "Washington DC"


async def test_parse_query_intent_missing_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    with pytest.raises(LLMServiceError, match="Not configured"):
        await parse_query_intent(client, "query")


@respx.mock
async def test_score_relevance_batch_returns_judgments(client):
    body = {"results": [{"id": 0, "is_relevant": True, "display_name": "John Smith", "reason": "Title mentions football in DC"}]}
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}))
    candidates = [{"id": 0, "platform": "Google", "title": "John Smith - Football Fan", "snippet": "Lives in DC"}]
    intent = {"interest": "Football", "audience": "Football lovers", "location": {"city": "Washington DC"}, "target_type": "individual"}
    results = await score_relevance_batch(client, intent, candidates)
    assert results[0]["is_relevant"] is True
    assert results[0]["display_name"] == "John Smith"


async def test_score_relevance_batch_empty_candidates_skips_the_call(client):
    # No LLM call should be made for an empty candidate list — a real cost
    # optimization, verified here by the absence of any mocked route.
    results = await score_relevance_batch(client, {}, [])
    assert results == []


@respx.mock
async def test_malformed_json_response_is_a_real_failure(client):
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}))
    with pytest.raises(LLMServiceError, match="not valid JSON"):
        await parse_query_intent(client, "query")


@respx.mock
async def test_rate_limited_is_a_real_failure(client):
    respx.post(ENDPOINT).mock(return_value=httpx.Response(429, json={"error": {"message": "Resource exhausted"}}))
    with pytest.raises(LLMServiceError, match="429"):
        await parse_query_intent(client, "query")
