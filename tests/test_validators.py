from __future__ import annotations

import pytest

from app.utils.validators import validate_query


def test_valid_query_passes():
    assert validate_query("Football lovers in Washington DC") == "Football lovers in Washington DC"


def test_empty_query_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        validate_query("")


def test_whitespace_only_query_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        validate_query("   ")


def test_over_length_query_rejected():
    with pytest.raises(ValueError, match="at most 300"):
        validate_query("a" * 301)
