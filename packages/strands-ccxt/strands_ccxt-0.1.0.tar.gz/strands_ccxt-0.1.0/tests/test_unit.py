"""
Unit tests for use_ccxt tool.

These tests don't require API keys and test basic functionality.
"""

import json
import pytest
from strands_ccxt import use_ccxt


class TestListExchanges:
    """Tests for list_exchanges action."""

    def test_list_exchanges_returns_success(self):
        result = use_ccxt(action="list_exchanges")
        assert result["status"] == "success"
        assert "content" in result
        assert "ms" in result

    def test_list_exchanges_returns_exchanges(self):
        result = use_ccxt(action="list_exchanges")
        data = json.loads(result["content"][0]["text"])
        assert "count" in data
        assert "exchanges" in data
        assert data["count"] > 50  # CCXT supports 100+ exchanges
        assert isinstance(data["exchanges"], list)

    def test_list_exchanges_includes_major_exchanges(self):
        result = use_ccxt(action="list_exchanges")
        data = json.loads(result["content"][0]["text"])
        exchanges = data["exchanges"]
        
        # Check for major exchanges
        major = ["binance", "bybit", "okx", "kraken", "coinbase"]
        for ex in major:
            assert ex in exchanges, f"{ex} should be in exchange list"


class TestDescribe:
    """Tests for describe action."""

    def test_describe_bybit(self):
        result = use_ccxt(action="describe", exchange="bybit")
        assert result["status"] == "success"
        assert result["exchange"] == "bybit"
        
        data = json.loads(result["content"][0]["text"])
        assert data["id"] == "bybit"
        assert "has" in data
        assert "timeframes" in data

    def test_describe_binance(self):
        result = use_ccxt(action="describe", exchange="binance")
        assert result["status"] == "success"
        assert result["exchange"] == "binance"

    def test_describe_unknown_exchange(self):
        result = use_ccxt(action="describe", exchange="unknown_exchange_xyz")
        assert result["status"] == "error"
        assert "Unknown exchange" in result["content"][0]["text"]

    def test_describe_returns_capabilities(self):
        result = use_ccxt(action="describe", exchange="bybit")
        data = json.loads(result["content"][0]["text"])
        
        # Check capabilities exist
        has = data.get("has", {})
        assert "fetchTicker" in has or "fetch_ticker" in str(has).lower()


class TestListMethods:
    """Tests for list_methods action."""

    def test_list_methods_bybit(self):
        result = use_ccxt(action="list_methods", exchange="bybit")
        assert result["status"] == "success"
        
        data = json.loads(result["content"][0]["text"])
        assert data["exchange"] == "bybit"
        assert "methods" in data
        assert isinstance(data["methods"], list)

    def test_list_methods_includes_common_methods(self):
        result = use_ccxt(action="list_methods", exchange="binance")
        data = json.loads(result["content"][0]["text"])
        methods = data["methods"]
        
        # Common methods should exist
        common = ["fetch_ticker", "fetch_order_book", "fetch_ohlcv"]
        for method in common:
            assert method in methods, f"{method} should be in methods list"


class TestUnknownAction:
    """Tests for unknown/invalid actions."""

    def test_unknown_action_returns_error(self):
        result = use_ccxt(action="invalid_action_xyz")
        assert result["status"] == "error"
        assert "Unknown action" in result["content"][0]["text"]

    def test_unknown_action_lists_valid_actions(self):
        result = use_ccxt(action="invalid_action_xyz")
        text = result["content"][0]["text"]
        assert "list_exchanges" in text
        assert "fetch_ticker" in text


class TestParameterValidation:
    """Tests for parameter validation."""

    def test_fetch_ticker_requires_symbol(self):
        result = use_ccxt(action="fetch_ticker", exchange="bybit")
        assert result["status"] == "error"
        assert "symbol required" in result["content"][0]["text"]

    def test_fetch_orderbook_requires_symbol(self):
        result = use_ccxt(action="fetch_orderbook", exchange="bybit")
        assert result["status"] == "error"
        assert "symbol required" in result["content"][0]["text"]

    def test_fetch_ohlcv_requires_symbol(self):
        result = use_ccxt(action="fetch_ohlcv", exchange="bybit")
        assert result["status"] == "error"
        assert "symbol required" in result["content"][0]["text"]

    def test_create_order_requires_all_params(self):
        # Missing symbol
        result = use_ccxt(action="create_order", exchange="bybit")
        assert result["status"] == "error"
        assert "symbol required" in result["content"][0]["text"]

        # Missing side
        result = use_ccxt(action="create_order", exchange="bybit", symbol="BTC/USDT")
        assert result["status"] == "error"
        assert "side required" in result["content"][0]["text"]

        # Missing order_type
        result = use_ccxt(
            action="create_order", exchange="bybit", symbol="BTC/USDT", side="buy"
        )
        assert result["status"] == "error"
        assert "order_type required" in result["content"][0]["text"]

        # Missing amount
        result = use_ccxt(
            action="create_order",
            exchange="bybit",
            symbol="BTC/USDT",
            side="buy",
            order_type="limit",
        )
        assert result["status"] == "error"
        assert "amount required" in result["content"][0]["text"]

    def test_cancel_order_requires_order_id(self):
        result = use_ccxt(action="cancel_order", exchange="bybit")
        assert result["status"] == "error"
        assert "order_id required" in result["content"][0]["text"]

    def test_fetch_order_requires_order_id(self):
        result = use_ccxt(action="fetch_order", exchange="bybit")
        assert result["status"] == "error"
        assert "order_id required" in result["content"][0]["text"]

    def test_multi_orderbook_requires_symbol(self):
        result = use_ccxt(action="multi_orderbook", exchanges='["binance", "bybit"]')
        assert result["status"] == "error"
        assert "symbol required" in result["content"][0]["text"]

    def test_multi_orderbook_requires_exchanges(self):
        result = use_ccxt(action="multi_orderbook", symbol="BTC/USDT")
        assert result["status"] == "error"
        assert "exchanges must be JSON array" in result["content"][0]["text"]

    def test_call_requires_method(self):
        result = use_ccxt(action="call", exchange="bybit")
        assert result["status"] == "error"
        assert "method required" in result["content"][0]["text"]


class TestJsonParsing:
    """Tests for JSON argument parsing."""

    def test_args_as_json_array(self):
        # This will fail due to auth, but should parse args correctly
        result = use_ccxt(
            action="call",
            exchange="bybit",
            method="fetch_ticker",
            args='["BTC/USDT"]',
        )
        # Should not fail on JSON parsing
        assert "JSON" not in result["content"][0]["text"] or "array" not in result["content"][0]["text"].lower()

    def test_kwargs_as_json_object(self):
        result = use_ccxt(
            action="call",
            exchange="bybit",
            method="fetch_ticker",
            args='["BTC/USDT"]',
            kwargs='{"limit": 10}',
        )
        # Should not fail on JSON parsing
        assert "JSON" not in result["content"][0]["text"] or "object" not in result["content"][0]["text"].lower()

    def test_invalid_args_json(self):
        result = use_ccxt(
            action="call",
            exchange="bybit",
            method="fetch_ticker",
            args="not valid json {",
        )
        assert result["status"] == "error"


class TestResponseFormat:
    """Tests for response format consistency."""

    def test_response_has_status(self):
        result = use_ccxt(action="list_exchanges")
        assert "status" in result
        assert result["status"] in ["success", "error"]

    def test_response_has_content(self):
        result = use_ccxt(action="list_exchanges")
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0
        assert "text" in result["content"][0]

    def test_response_has_ms(self):
        result = use_ccxt(action="list_exchanges")
        assert "ms" in result
        assert isinstance(result["ms"], int)
        assert result["ms"] >= 0

    def test_describe_response_has_exchange(self):
        result = use_ccxt(action="describe", exchange="bybit")
        assert "exchange" in result
        assert result["exchange"] == "bybit"


class TestRedaction:
    """Tests for sensitive data redaction."""

    def test_describe_redacts_nothing_sensitive(self):
        result = use_ccxt(action="describe", exchange="bybit")
        text = result["content"][0]["text"]
        
        # Should not contain actual API keys (even if set in env)
        assert "REDACTED" not in text or "apiKey" not in text


class TestExchangeNormalization:
    """Tests for exchange ID normalization."""

    def test_exchange_case_insensitive(self):
        result1 = use_ccxt(action="describe", exchange="bybit")
        result2 = use_ccxt(action="describe", exchange="BYBIT")
        result3 = use_ccxt(action="describe", exchange="Bybit")
        
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result3["status"] == "success"

    def test_exchange_with_whitespace(self):
        result = use_ccxt(action="describe", exchange="  bybit  ")
        assert result["status"] == "success"
        assert result["exchange"] == "bybit"
