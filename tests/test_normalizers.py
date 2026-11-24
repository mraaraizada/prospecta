from __future__ import annotations

from app.utils.normalizers import extract_email, extract_phone, extract_whatsapp_link, normalize_name


def test_extract_email_finds_real_address():
    assert extract_email("Contact us at john.smith@example.com for info") == "john.smith@example.com"


def test_extract_email_returns_none_when_absent():
    assert extract_email("No contact info here") is None


def test_extract_phone_finds_real_number():
    assert extract_phone("Call +1 202-555-0147 today") is not None


def test_extract_phone_rejects_short_digit_sequences():
    # A year or a small ID shouldn't be mistaken for a phone number.
    assert extract_phone("Founded in 2024") is None


def test_extract_whatsapp_link_finds_real_link():
    assert extract_whatsapp_link("Message us: https://wa.me/12025550147") == "https://wa.me/12025550147"


def test_extract_whatsapp_link_returns_none_when_absent():
    assert extract_whatsapp_link("No WhatsApp here") is None


def test_normalize_name_is_case_and_punctuation_insensitive():
    assert normalize_name("John  Smith") == normalize_name("john smith.")
    assert normalize_name("O'Brien") == normalize_name("obrien")


def test_normalize_name_distinguishes_different_names():
    assert normalize_name("John Smith") != normalize_name("Jane Smith")
