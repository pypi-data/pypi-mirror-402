"""
Integration tests for use_ccxt tool.

These tests require valid API credentials and make real API calls.
Skip these tests if credentials are not available.

To run: CCXT_EXCHANGE=bybit CCXT_API_KEY=xxx CCXT_SECRET=xxx pytest tests/test_integration.py -v
"""

import json
import os
import pytest
from strands_ccxt import use_ccxt


# Skip all tests if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("CCXT_API_KEY") or not os.getenv("CCXT_SECRET"),
    reason="CCXT_API_KEY and CCXT_SECRET required for integration tests"
)


class TestMarketData:
    """Integration tests for market data endpoints."""

    def test_fetch_ticker(self):
        result = use_ccxt(action="fetch_ticker", symbol="BTC/USDT")
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        assert "symbol" in data
        assert "last" in data
        assert "bid" in data
        assert "ask" in data
        assert data["symbol"] == "BTC/USDT"
        assert data["last"] > 0

    def test_fetch_orderbook(self):
        result = use_ccxt(action="fetch_orderbook", symbol="BTC/USDT", limit=10)
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        assert "bids" in data
        assert "asks" in data
        assert len(data["bids"]) > 0
        assert len(data["asks"]) > 0

    def test_fetch_ohlcv(self):
        result = use_ccxt(
            action="fetch_ohlcv",
            symbol="BTC/USDT",
            timeframe="1h",
            limit=10
        )
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        assert "candles" in data
        assert data["count"] == 10
        assert data["timeframe"] == "1h"
        
        candle = data["candles"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle

    def test_fetch_trades(self):
        result = use_ccxt(action="fetch_trades", symbol="BTC/USDT", limit=10)
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        assert result["count"] <= 10

    def test_load_markets(self):
        result = use_ccxt(action="load_markets")
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        assert "count" in data
        assert "symbols" in data
        assert data["count"] > 0
        assert "BTC/USDT" in data["symbols"] or "BTC/USDT:USDT" in data["symbols"]


class TestAccountData:
    """Integration tests for account endpoints (require valid auth)."""

    def test_fetch_balance(self):
        result = use_ccxt(action="fetch_balance")
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "AuthenticationError" in error_text or "invalid" in error_text.lower():
                pytest.skip("Invalid API credentials")
            pytest.fail(f"Unexpected error: {error_text}")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        # Balance should have timestamp
        assert "timestamp" in data or "datetime" in data

    def test_fetch_positions(self):
        result = use_ccxt(action="fetch_positions")
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "AuthenticationError" in error_text or "invalid" in error_text.lower():
                pytest.skip("Invalid API credentials")
            if "not supported" in error_text.lower():
                pytest.skip("Exchange does not support fetch_positions")
            pytest.fail(f"Unexpected error: {error_text}")
        
        assert result["status"] == "success"

    def test_fetch_open_orders(self):
        result = use_ccxt(action="fetch_open_orders", symbol="BTC/USDT")
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "AuthenticationError" in error_text or "invalid" in error_text.lower():
                pytest.skip("Invalid API credentials")
            pytest.fail(f"Unexpected error: {error_text}")
        
        assert result["status"] == "success"


class TestMultiExchange:
    """Integration tests for multi-exchange operations."""

    def test_multi_orderbook(self):
        result = use_ccxt(
            action="multi_orderbook",
            exchanges='["binance", "bybit"]',
            symbol="BTC/USDT"
        )
        
        # This may fail for individual exchanges but should return results
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        assert "symbol" in data
        assert "exchanges" in data
        assert "best_bid" in data
        assert "best_ask" in data
        assert len(data["exchanges"]) == 2


class TestGenericCall:
    """Integration tests for generic call action."""

    def test_call_fetch_ticker(self):
        result = use_ccxt(
            action="call",
            method="fetch_ticker",
            args='["BTC/USDT"]'
        )
        
        if result["status"] == "error" and "AuthenticationError" in result["content"][0]["text"]:
            pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        assert result["method"] == "fetch_ticker"

    def test_call_unknown_method(self):
        result = use_ccxt(
            action="call",
            method="unknown_method_xyz",
            args='[]'
        )
        
        assert result["status"] == "error"
        assert "no method" in result["content"][0]["text"].lower()


class TestWebSocket:
    """Integration tests for WebSocket streaming (requires ccxt.pro)."""

    @pytest.mark.skipif(
        True,  # Skip by default as it requires ccxt.pro
        reason="WebSocket tests require ccxt.pro installation"
    )
    def test_watch_ticker(self):
        result = use_ccxt(
            action="watch_ticker",
            symbol="BTC/USDT",
            max_messages=2,
            max_seconds=10
        )
        
        if result["status"] == "error":
            if "not installed" in result["content"][0]["text"].lower():
                pytest.skip("ccxt.pro not installed")
            if "AuthenticationError" in result["content"][0]["text"]:
                pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        assert data["count"] > 0
