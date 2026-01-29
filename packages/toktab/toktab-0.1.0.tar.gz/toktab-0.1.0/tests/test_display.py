"""Tests for the display formatting module."""

import pytest

from toktab.display import format_cost, format_tokens, get_cost_style


class TestFormatCost:
    def test_none_returns_dash(self):
        assert format_cost(None) == "-"

    def test_zero_returns_free(self):
        assert format_cost(0) == "Free"

    def test_very_small_cost(self):
        # $0.0000005 per token = $0.50 per million
        result = format_cost(0.0000005)
        assert result == "$0.5"

    def test_small_cost(self):
        # $0.000001 per token = $1 per million
        result = format_cost(0.000001)
        assert result == "$1.00"

    def test_larger_cost(self):
        # $0.00006 per token = $60 per million
        result = format_cost(0.00006)
        assert result == "$60.00"

    def test_tiny_cost(self):
        # $0.00000001 per token = $0.01 per million
        result = format_cost(0.00000001)
        assert result == "$0.01"


class TestFormatTokens:
    def test_none_returns_dash(self):
        assert format_tokens(None) == "-"

    def test_small_number(self):
        assert format_tokens(500) == "500"

    def test_thousands(self):
        assert format_tokens(8000) == "8K"
        assert format_tokens(128000) == "128K"

    def test_millions(self):
        assert format_tokens(1000000) == "1M"
        assert format_tokens(2000000) == "2M"

    def test_removes_trailing_zeros(self):
        assert format_tokens(8192) == "8.2K"


class TestGetCostStyle:
    def test_none_is_green(self):
        assert get_cost_style(None) == "green"

    def test_zero_is_green(self):
        assert get_cost_style(0) == "green"

    def test_low_cost_is_green(self):
        # Less than $1 per million
        assert get_cost_style(0.0000005) == "green"

    def test_medium_cost_is_yellow(self):
        # Between $1 and $10 per million
        assert get_cost_style(0.000005) == "yellow"

    def test_high_cost_is_red(self):
        # More than $10 per million
        assert get_cost_style(0.00002) == "red"
