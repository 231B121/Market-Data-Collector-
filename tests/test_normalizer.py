"""Tests for app.services.normalizer."""

from datetime import timedelta

import pytest

from app.models import MarketRecord
from app.services.normalizer import (
    NormalizationError,
    calculate_spread,
    normalize_market_item,
)


def test_valid_market_data_is_normalized(btc_item, fixed_time):
    record = normalize_market_item(btc_item, latency_ms=720.2, polled_at=fixed_time)

    assert record.symbol == "BTC-USD"
    assert record.exchange == "coingecko"
    assert record.price == pytest.approx(68839.0)
    assert record.volume_24h == pytest.approx(43317702456.0)
    assert record.price_change_24h_pct == pytest.approx(-4.17483)
    assert record.api_latency_ms == pytest.approx(720.2)
    assert record.polled_at == fixed_time
    assert record.raw_response_id is None


def test_symbol_is_uppercase_and_dash_separated(btc_item):
    for raw, expected in [("btc", "BTC-USD"), ("eth", "ETH-USD"), (" sol ", "SOL-USD")]:
        btc_item["symbol"] = raw
        assert normalize_market_item(btc_item, 1.0).symbol == expected


def test_spread_when_bid_and_ask_exist():
    spread, _ = calculate_spread(100, 102)
    assert spread == pytest.approx(2.0)


def test_spread_pct_calculation():
    # spread = 2, mid = 101, pct = 2 / 101 * 100
    _, spread_pct = calculate_spread(100, 102)
    assert spread_pct == pytest.approx(2 / 101 * 100)


def test_null_propagation_when_bid_missing():
    assert calculate_spread(None, 102) == (None, None)


def test_null_propagation_when_ask_missing():
    assert calculate_spread(100, None) == (None, None)


def test_missing_optional_api_values_become_none(btc_item):
    btc_item["total_volume"] = None
    del btc_item["price_change_percentage_24h"]

    record = normalize_market_item(btc_item, 1.0)

    assert record.volume_24h is None
    assert record.price_change_24h_pct is None
    assert record.price == pytest.approx(68839.0)  # required field still fine


def test_missing_price_raises(btc_item):
    btc_item["current_price"] = None
    with pytest.raises(NormalizationError):
        normalize_market_item(btc_item, 1.0)


def test_missing_symbol_raises(btc_item):
    del btc_item["symbol"]
    with pytest.raises(NormalizationError):
        normalize_market_item(btc_item, 1.0)


def test_zero_mid_price_gives_null_spread_pct():
    # bid=-1, ask=1 -> mid is 0 -> must not divide by zero
    spread, spread_pct = calculate_spread(-1, 1)
    assert spread == pytest.approx(2.0)
    assert spread_pct is None


def test_bid_and_ask_are_converted_to_float(btc_item):
    record = normalize_market_item(btc_item, 1.0, bid=100, ask=102)
    assert isinstance(record.bid, float)
    assert isinstance(record.ask, float)
    assert isinstance(record.spread, float)


def test_polled_at_is_utc(btc_item):
    record = normalize_market_item(btc_item, 1.0)
    assert record.polled_at.tzinfo is not None
    assert record.polled_at.utcoffset() == timedelta(0)


def test_record_has_exactly_the_required_fields(btc_item):
    record = normalize_market_item(btc_item, 1.0)
    assert isinstance(record, MarketRecord)
    assert set(record.to_dict()) == {
        "symbol", "exchange", "price", "bid", "ask", "spread", "spread_pct",
        "volume_24h", "price_change_24h_pct", "api_latency_ms",
        "polled_at", "raw_response_id",
    }