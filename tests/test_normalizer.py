"""Tests for market data normalization and spread calculations."""

from datetime import datetime, timezone

import pytest

from app.models import MarketRecord
from app.services.normalizer import (
    NormalizationError,
    calculate_spread,
    normalize_market_item,
)


def test_calculate_spread_valid():
    spread, spread_pct = calculate_spread(100.0, 102.0)
    assert spread == pytest.approx(2.0)
    assert spread_pct == pytest.approx(2.0 / 101.0 * 100)


def test_calculate_spread_missing():
    assert calculate_spread(None, 100.0) == (None, None)
    assert calculate_spread(100.0, None) == (None, None)
    assert calculate_spread(None, None) == (None, None)


def test_calculate_spread_zero_mid_price():
    spread, spread_pct = calculate_spread(-10.0, 10.0)
    assert spread == 20.0
    assert spread_pct is None


def test_normalize_market_item_success():
    item = {
        "id": "bitcoin",
        "symbol": "btc",
        "current_price": 68839.5,
        "total_volume": 43317702456,
        "price_change_percentage_24h": -4.17483,
    }
    now = datetime.now(timezone.utc)
    record = normalize_market_item(item, latency_ms=125.5, polled_at=now, bid=68830.0, ask=68840.0)

    assert isinstance(record, MarketRecord)
    assert record.symbol == "BTC-USD"
    assert record.exchange == "coingecko"
    assert record.price == 68839.5
    assert record.bid == 68830.0
    assert record.ask == 68840.0
    assert record.spread == pytest.approx(10.0)
    assert record.volume_24h == 43317702456.0
    assert record.price_change_24h_pct == pytest.approx(-4.17483)
    assert record.api_latency_ms == 125.5
    assert record.polled_at == now

    data = record.to_dict()
    assert data["symbol"] == "BTC-USD"
    assert data["polled_at"] == now.isoformat()


def test_normalize_market_item_missing_symbol():
    item = {"current_price": 100.0}
    with pytest.raises(NormalizationError, match="Missing or invalid 'symbol'"):
        normalize_market_item(item, latency_ms=10.0)


def test_normalize_market_item_missing_price():
    item = {"symbol": "eth", "current_price": None}
    with pytest.raises(NormalizationError, match="Missing or invalid 'current_price'"):
        normalize_market_item(item, latency_ms=10.0)
