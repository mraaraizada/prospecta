"""Relevance filtering and duplicate-consolidation tests. respx-mocked where an
LLM call is involved."""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.config import settings
from app.platforms.base import RawCandidate
from app.services.deduplication_service import consolidate
from app.services.profile_extractor import extract_profile
from app.services.relevance_service import filter_relevant

ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"


@pytest.fixture
def client():
    return httpx.AsyncClient()


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")


@respx.mock
async def test_filter_relevant_excludes_llm_rejected_candidates(client):
    body = {
        "results": [
            {"id": 0, "is_relevant": True, "display_name": "John Smith", "reason": "Matches"},
            {"id": 1, "is_relevant": False, "display_name": "", "reason": "No connection to football or DC"},
        ]
    }
    respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}))
    candidates = [
        RawCandidate(platform="Google", title="John Smith - Football Fan DC", snippet="...", link="https://example.com/john"),
        RawCandidate(platform="Google", title="Unrelated Page", snippet="...", link="https://example.com/other"),
    ]
    kept = await filter_relevant(client, {}, candidates)
    assert len(kept) == 1
    assert kept[0]["display_name"] == "John Smith"


async def test_filter_relevant_empty_candidates_returns_empty(client):
    assert await filter_relevant(client, {}, []) == []


def test_extract_profile_pulls_real_contact_info_from_snippet():
    relevant_item = {
        "candidate": RawCandidate(platform="Google", title="John Smith", snippet="Email: john@example.com Call +1 202-555-0147", link="https://example.com/john"),
        "display_name": "John Smith",
        "reason": "...",
    }
    hit = extract_profile(relevant_item)
    assert hit["email"] == "john@example.com"
    assert hit["phone"] is not None


def test_consolidate_merges_exact_normalized_name_matches():
    hits = [
        {"display_name": "John Smith", "platform": "LinkedIn", "link": "https://linkedin.com/in/johnsmith", "email": None, "phone": None, "whatsapp_link": None},
        {"display_name": "john smith", "platform": "Instagram", "link": "https://instagram.com/johnsmith", "email": "john@example.com", "phone": None, "whatsapp_link": None},
    ]
    prospects = consolidate(hits, "Washington DC, USA")
    assert len(prospects) == 1
    assert prospects[0].name == "John Smith"
    assert len(prospects[0].social_link) == 3  # LinkedIn + Instagram + Email
    platforms = {sl.platform for sl in prospects[0].social_link}
    assert platforms == {"LinkedIn", "Instagram", "Email"}


def test_consolidate_keeps_different_names_separate():
    hits = [
        {"display_name": "John Smith", "platform": "LinkedIn", "link": "https://linkedin.com/in/johnsmith", "email": None, "phone": None, "whatsapp_link": None},
        {"display_name": "Jane Smith", "platform": "LinkedIn", "link": "https://linkedin.com/in/janesmith", "email": None, "phone": None, "whatsapp_link": None},
    ]
    prospects = consolidate(hits, None)
    assert len(prospects) == 2


def test_consolidate_deduplicates_identical_links():
    hits = [
        {"display_name": "John Smith", "platform": "LinkedIn", "link": "https://linkedin.com/in/johnsmith", "email": None, "phone": None, "whatsapp_link": None},
        {"display_name": "John Smith", "platform": "LinkedIn", "link": "https://linkedin.com/in/johnsmith", "email": None, "phone": None, "whatsapp_link": None},
    ]
    prospects = consolidate(hits, None)
    assert len(prospects) == 1
    assert len(prospects[0].social_link) == 1
