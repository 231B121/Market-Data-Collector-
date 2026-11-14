"""Tests for app.repository (no real database)."""

from unittest.mock import MagicMock

import psycopg
import pytest

from app import repository
from app.repository import MarketRepository, RepositoryError
from app.services.normalizer import normalize_market_item


def fake_conn() -> MagicMock:
    conn = MagicMock()
    conn.__enter__.return_value = conn
    return conn


@pytest.fixture
def record(btc_item):
    return normalize_market_item(btc_item, latency_ms=12.5)


def test_save_sends_all_fields_and_none_stays_none(monkeypatch, record):
    conn = fake_conn()
    monkeypatch.setattr(repository.psycopg, "connect", lambda *a, **k: conn)

    MarketRepository("postgresql://fake").save(record)

    sql, params = conn.execute.call_args.args
    assert "INSERT INTO market_records" in sql
    assert params["symbol"] == "BTC-USD"
    assert params["bid"] is None
    assert len(params) == 12


def test_save_wraps_database_errors(monkeypatch, record):
    def boom(*a, **k):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(repository.psycopg, "connect", boom)

    with pytest.raises(RepositoryError, match="Could not save"):
        MarketRepository("postgresql://fake").save(record)


def test_get_latest_passes_symbol_and_limit(monkeypatch):
    conn = fake_conn()
    conn.execute.return_value.fetchall.return_value = [{"symbol": "BTC-USD"}]
    monkeypatch.setattr(repository.psycopg, "connect", lambda *a, **k: conn)

    rows = MarketRepository("postgresql://fake").get_latest("BTC-USD", 5)

    assert rows == [{"symbol": "BTC-USD"}]
    assert conn.execute.call_args.args[1] == ("BTC-USD", 5)