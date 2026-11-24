"""Turns a parsed query intent into the actual search-term string every platform
searcher uses (each platform then adds its own `site:` filter on top)."""
from __future__ import annotations


def build_search_terms(intent: dict) -> str:
    location = intent.get("location") or {}
    parts = [intent.get("interest", ""), intent.get("audience", "")]
    parts += [location.get("city") or "", location.get("state") or "", location.get("country") or ""]
    return " ".join(p for p in parts if p).strip()
