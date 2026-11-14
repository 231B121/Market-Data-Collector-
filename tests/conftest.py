"""Shared pytest fixtures."""

from datetime import datetime, timezone

import pytest


@pytest.fixture
def btc_item() -> dict:
    """A mocked CoinGecko /coins/markets item (shape copied from the real API)."""
    return {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 68839,
        "total_volume": 43317702456,
        "price_change_percentage_24h": -4.17483,
    }


@pytest.fixture
def fixed_time() -> datetime:
    """A fixed UTC timestamp so tests are deterministic."""
    return datetime(2026, 11, 13, 18, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def valid_env() -> dict:
    """The minimum valid environment: only the required DB_URL."""
    return {"DB_URL": "postgresql://user:password@localhost:5432/market_data"}