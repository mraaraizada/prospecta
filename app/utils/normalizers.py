"""Pure, dependency-free helpers: extracting publicly-visible contact info that's
ALREADY present in a candidate's own title/snippet text (never invented or
pattern-guessed), and normalizing a name for duplicate-detection grouping."""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
#: A conservative international-phone shape: optional +, 7-15 digits, allowing
#: common separators — deliberately strict to avoid matching a date, an ID
#: number, or a price as if it were a phone number.
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,14}\d")
_WA_LINK_RE = re.compile(r"https?://wa\.me/\d+\S*")


def extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(0))
    # Reject anything that isn't a plausible phone-number digit count.
    if not (7 <= len(digits) <= 15):
        return None
    return match.group(0).strip()


def extract_whatsapp_link(text: str) -> str | None:
    match = _WA_LINK_RE.search(text)
    return match.group(0) if match else None


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/extra whitespace — used only to GROUP
    candidates for consolidation, never shown to the user (the real, original
    display_name is always what's returned)."""
    cleaned = re.sub(r"[^\w\s]", "", name.lower())
    return " ".join(cleaned.split())
