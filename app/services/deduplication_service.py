"""Consolidates profile hits belonging to the same individual/business into one
Prospect record with multiple social_link entries.

Consolidation rule, deliberately conservative per the spec's explicit warning to
"avoid merging different individuals with similar names": two hits are merged
only when their normalized display names match EXACTLY (see
app/utils/normalizers.py's normalize_name). This is a real, honest limitation —
it will under-merge two profiles that use meaningfully different name spellings
across platforms — documented in the README rather than hidden behind a fuzzier
heuristic that risks the opposite, more harmful failure: merging two different
people who happen to share a name.
"""
from __future__ import annotations

from app.schemas import Prospect, SocialLink
from app.services.profile_extractor import ProfileHit
from app.utils.normalizers import normalize_name


def consolidate(hits: list[ProfileHit], location_label: str | None) -> list[Prospect]:
    groups: dict[str, list[ProfileHit]] = {}
    order: list[str] = []
    for hit in hits:
        key = normalize_name(hit["display_name"])
        if not key:
            continue
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(hit)

    prospects = []
    for key in order:
        group = groups[key]
        display_name = group[0]["display_name"]  # first real, LLM-extracted name seen for this group
        social_links: list[SocialLink] = []
        seen_links: set[str] = set()
        seen_emails: set[str] = set()
        seen_phones: set[str] = set()
        seen_whatsapp: set[str] = set()

        for hit in group:
            if hit["link"] and hit["link"] not in seen_links:
                social_links.append(SocialLink(platform=hit["platform"], link=hit["link"]))
                seen_links.add(hit["link"])
            if hit["email"] and hit["email"] not in seen_emails:
                social_links.append(SocialLink(platform="Email", link=f"mailto:{hit['email']}"))
                seen_emails.add(hit["email"])
            if hit["phone"] and hit["phone"] not in seen_phones:
                social_links.append(SocialLink(platform="Phone", link=hit["phone"]))
                seen_phones.add(hit["phone"])
            if hit["whatsapp_link"] and hit["whatsapp_link"] not in seen_whatsapp:
                social_links.append(SocialLink(platform="WhatsApp", link=hit["whatsapp_link"]))
                seen_whatsapp.add(hit["whatsapp_link"])

        prospects.append(Prospect(name=display_name, location=location_label, social_link=social_links))

    return prospects
