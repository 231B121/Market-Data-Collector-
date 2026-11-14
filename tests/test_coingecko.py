"""Tests for CoinGecko API client (no live network calls)."""

from unittest.mock import MagicMock

import httpx
import pytest

from app.clients.coingecko import CoinGeckoClient, CoinGeckoError, MarketsResponse


def make_client(json_data=None, get_error=None, status_error=None, json_error=None):
    """Build a CoinGeckoClient whose HTTP layer is fully mocked."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    if json_error is not None:
        mock_response.json.side_effect = json_error
    if status_error is not None:
        mock_response.raise_for_status.side_effect = status_error

    mock_client = MagicMock(spec=httpx.Client)
    if get_error is not None:
        mock_client.get.side_effect = get_error
    else:
        mock_client.get.return_value = mock_response
    return CoinGeckoClient(client=mock_client)


def status_error(status: int) -> httpx.HTTPStatusError:
    response = MagicMock()
    response.status_code = status
    return httpx.HTTPStatusError("err", request=MagicMock(), response=response)


def test_fetch_markets_success():
    client = make_client(
        json_data=[
            {"id": "bitcoin", "symbol": "btc", "current_price": 68000.0},
            {"id": "ethereum", "symbol": "eth", "current_price": 3500.0},
        ]
    )

    res = client.fetch_markets(["bitcoin", "ethereum"])

    assert isinstance(res, MarketsResponse)
    assert len(res.data) == 2
    assert res.data[0]["id"] == "bitcoin"
    assert res.latency_ms >= 0


def test_fetch_markets_empty_coins():
    client = make_client()
    with pytest.raises(CoinGeckoError, match="coin_ids must not be empty") as exc_info:
        client.fetch_markets([])
    assert exc_info.value.retryable is False


def test_fetch_markets_timeout():
    client = make_client(get_error=httpx.TimeoutException("timeout"))
    with pytest.raises(CoinGeckoError, match="Request timed out") as exc_info:
        client.fetch_markets(["bitcoin"])
    assert exc_info.value.retryable is True


def test_fetch_markets_network_error_is_retryable():
    client = make_client(get_error=httpx.ConnectError("refused"))
    with pytest.raises(CoinGeckoError, match="Network error") as exc_info:
        client.fetch_markets(["bitcoin"])
    assert exc_info.value.retryable is True


def test_fetch_markets_http_error_message():
    client = make_client(status_error=status_error(429))
    with pytest.raises(CoinGeckoError, match="CoinGecko returned HTTP 429"):
        client.fetch_markets(["bitcoin"])


@pytest.mark.parametrize(
    "status,expected",
    [(429, True), (500, True), (503, True), (400, False), (404, False)],
)
def test_retryable_depends_on_status(status, expected):
    client = make_client(status_error=status_error(status))
    with pytest.raises(CoinGeckoError) as exc_info:
        client.fetch_markets(["bitcoin"])
    assert exc_info.value.retryable is expected


def test_fetch_markets_invalid_json():
    client = make_client(json_error=ValueError("Invalid JSON"))
    with pytest.raises(CoinGeckoError, match="Response was not valid JSON") as exc_info:
        client.fetch_markets(["bitcoin"])
    assert exc_info.value.retryable is False


def test_fetch_markets_non_list_response_raises():
    client = make_client(json_data={"error": "something"})
    with pytest.raises(CoinGeckoError, match="Expected a list") as exc_info:
        client.fetch_markets(["bitcoin"])
    assert exc_info.value.retryable is False


def test_fetch_markets_warns_about_missing_coins(caplog):
    client = make_client(json_data=[{"id": "bitcoin", "symbol": "btc"}])

    with caplog.at_level("WARNING"):
        res = client.fetch_markets(["bitcoin", "typo-coin"])

    assert len(res.data) == 1
    assert "typo-coin" in caplog.text