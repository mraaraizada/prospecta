"""Turns an LLM-confirmed-relevant candidate into a normalized profile hit,
extracting any publicly-visible contact info already present in its title/snippet
text (never invented — see app/utils/normalizers.py)."""
from __future__ import annotations

from app.utils.normalizers import extract_email, extract_phone, extract_whatsapp_link


class ProfileHit(dict):
    """display_name, platform, link, email, phone, whatsapp_link — any of the
    last three may be None if nothing was found in the candidate's own text."""


def extract_profile(relevant_item: dict) -> ProfileHit:
    candidate = relevant_item["candidate"]
    text = f"{candidate['title']} {candidate['snippet']}"
    return ProfileHit(
        display_name=relevant_item["display_name"],
        platform=candidate["platform"],
        link=candidate["link"],
        email=extract_email(text),
        phone=extract_phone(text),
        whatsapp_link=extract_whatsapp_link(text),
    )
