"""Tests for CoinGecko API client."""

from unittest.mock import MagicMock

import httpx
import pytest

from app.clients.coingecko import CoinGeckoClient, CoinGeckoError, MarketsResponse


def test_fetch_markets_success():
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"id": "bitcoin", "symbol": "btc", "current_price": 68000.0},
        {"id": "ethereum", "symbol": "eth", "current_price": 3500.0},
    ]
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    client = CoinGeckoClient(client=mock_client)
    res = client.fetch_markets(["bitcoin", "ethereum"])

    assert isinstance(res, MarketsResponse)
    assert len(res.data) == 2
    assert res.data[0]["id"] == "bitcoin"
    assert res.latency_ms >= 0


def test_fetch_markets_empty_coins():
    client = CoinGeckoClient()
    with pytest.raises(CoinGeckoError, match="coin_ids must not be empty"):
        client.fetch_markets([])


def test_fetch_markets_timeout():
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.TimeoutException("timeout")

    client = CoinGeckoClient(client=mock_client)
    with pytest.raises(CoinGeckoError, match="Request timed out"):
        client.fetch_markets(["bitcoin"])


def test_fetch_markets_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_response)

    client = CoinGeckoClient(client=mock_client)
    with pytest.raises(CoinGeckoError, match="CoinGecko returned HTTP 429"):
        client.fetch_markets(["bitcoin"])


def test_fetch_markets_invalid_json():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    client = CoinGeckoClient(client=mock_client)
    with pytest.raises(CoinGeckoError, match="Response was not valid JSON"):
        client.fetch_markets(["bitcoin"])
