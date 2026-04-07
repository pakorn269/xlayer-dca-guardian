import pytest
import sys
from unittest.mock import MagicMock

# Patch ollama so tests always use regex fallback
sys.modules["ollama"] = MagicMock(side_effect=Exception("no ollama"))

from main import parse_nl_query_local


def test_dollar_sign_stripped():
    result = parse_nl_query_local("DCA $50 USDC to ETH every week for 30 days")
    assert result["amount"] == 50.0


def test_daily_interval():
    result = parse_nl_query_local("DCA 10 USDC to ETH daily for 30 days")
    assert result["interval"] == 1


def test_biweekly_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH biweekly for 60 days")
    assert result["interval"] == 14


def test_every_other_week_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH every other week for 60 days")
    assert result["interval"] == 14


def test_quarterly_interval():
    result = parse_nl_query_local("DCA 100 USDC to ETH quarterly for 365 days")
    assert result["interval"] == 90


def test_every_x_weeks_interval():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 3 weeks for 90 days")
    assert result["interval"] == 21


def test_buy_x_with_y_word_order():
    result = parse_nl_query_local("buy BTC with 100 USDC every week for 30 days")
    assert result["token_out"] == "BTC"
    assert result["token_in"] == "USDC"


def test_same_token_returns_error():
    result = parse_nl_query_local("DCA 50 USDC to USDC every 7 days for 30 days")
    assert "error" in result


def test_interval_greater_than_duration_auto_swapped():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 30 days for 7 days")
    assert result["interval"] < result["duration"]


def test_zero_amount_returns_error():
    result = parse_nl_query_local("DCA 0 USDC to ETH every 7 days for 30 days")
    assert "error" in result


def test_parser_key_present():
    result = parse_nl_query_local("DCA 50 USDC to ETH every 7 days for 30 days")
    assert "parser" in result
    assert result["parser"] in ("ollama", "regex")


def test_bnb_token_recognized():
    result = parse_nl_query_local("DCA 50 USDC to BNB every week for 30 days")
    assert result["token_out"] == "BNB"


def test_link_token_recognized():
    result = parse_nl_query_local("DCA 50 USDC to LINK every week for 30 days")
    assert result["token_out"] == "LINK"


def test_wokb_token_recognized():
    result = parse_nl_query_local("DCA 50 USDC to WOKB every week for 30 days")
    assert result["token_out"] == "WOKB"
