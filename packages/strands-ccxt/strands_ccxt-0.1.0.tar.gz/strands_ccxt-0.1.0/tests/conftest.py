"""
Fixtures and configuration for pytest.
"""

import os
import pytest
from dotenv import load_dotenv


def pytest_configure(config):
    """Load .env file before tests."""
    # Try to load .env from project root
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)


@pytest.fixture
def exchange():
    """Default exchange for tests."""
    return os.getenv("CCXT_EXCHANGE", "bybit")


@pytest.fixture
def symbol():
    """Default trading symbol for tests."""
    return "BTC/USDT"
