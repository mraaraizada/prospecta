"""Opt-in live end-to-end test: real Gemini + real Google Custom Search + real
YouTube Data API calls, using the spec's own example queries.

Excluded from the default `pytest` run (see pytest.ini). Run explicitly with
`pytest -m live -v -s` once real credentials are in `.env`.
"""
from __future__ import annotations

import pytest

from app.config import settings
from app.services.prospect_service import discover_prospects

pytestmark = pytest.mark.live

_TEST_QUERIES = [
    "Football lovers in Washington DC in USA",
    "Digital marketing agency owners in New York USA",
    "Startup founders in London UK",
    "Cricket lovers in Ahmedabad India",
    "Restaurant owners in Dubai UAE",
]


@pytest.mark.parametrize("query", _TEST_QUERIES)
async def test_live_discovery_for_spec_test_query(query):
    if not settings.gemini_api_key:
        pytest.skip("GEMINI_API_KEY not configured")

    result = await discover_prospects(query)
    print(f"\n--- Live /prospect-discovery result for {query!r} ---")
    print(result.model_dump_json(indent=2))

    assert result.query == query
    if result.success:
        assert result.total_prospects == len(result.prospects)
    else:
        assert result.error
