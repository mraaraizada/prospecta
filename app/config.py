"""Environment-based configuration. All values default to None/empty so a missing
credential degrades that one platform/feature to a clean, explicit "not configured"
failure rather than crashing the whole application."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    gemini_model: str = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"

    #: Google Custom Search JSON API — https://programmablesearchengine.google.com/
    #: the real discovery engine for every platform without its own search API.
    google_cse_api_key: str | None = os.getenv("GOOGLE_CSE_API_KEY") or None
    google_cse_id: str | None = os.getenv("GOOGLE_CSE_ID") or None

    #: YouTube Data API v3 — https://console.cloud.google.com/apis/library/youtube.googleapis.com
    youtube_api_key: str | None = os.getenv("YOUTUBE_API_KEY") or None

    request_timeout_seconds: float = float(os.getenv("PROSPECTA_REQUEST_TIMEOUT", "15"))
    llm_timeout_seconds: float = float(os.getenv("PROSPECTA_LLM_TIMEOUT", "60"))

    #: Max search results requested per platform per discovery run — bounds cost
    #: and keeps the whole request within a reasonable response time.
    max_results_per_platform: int = int(os.getenv("PROSPECTA_MAX_RESULTS_PER_PLATFORM", "5"))


settings = Settings()
