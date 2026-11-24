"""Real-world-bug regression test: Gemini occasionally hallucinates a garbled
placeholder sentence into a location field instead of a real value or null
(observed verbatim during live testing on 2026-11-24, see
app/utils/normalizers.py's sanitize_location_part docstring)."""
from __future__ import annotations

from app.utils.normalizers import sanitize_location_part


def test_real_place_names_pass_through_unchanged():
    assert sanitize_location_part("Washington DC") == "Washington DC"
    assert sanitize_location_part("District of Columbia") == "District of Columbia"
    assert sanitize_location_part("USA") == "USA"


def test_none_and_empty_pass_through_as_none():
    assert sanitize_location_part(None) is None
    assert sanitize_location_part("") is None


def test_real_hallucinated_garbage_is_rejected():
    # The exact real value observed during live testing.
    garbage = "DCose/nullORotherIfNotExplicitlySeparatedStateElseNullOrWashingtonDCIsCityStateItselfOrSimilar-letSKeepStateNullAsCityIsWashington DC and Country is USA"
    assert sanitize_location_part(garbage) is None


def test_text_containing_null_literal_is_rejected():
    assert sanitize_location_part("null") is None
    assert sanitize_location_part("N/A") is None


def test_overlong_value_is_rejected():
    assert sanitize_location_part("a" * 41) is None
