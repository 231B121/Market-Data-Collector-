"""Tests for app.poller (all collaborators faked)."""

from unittest.mock import MagicMock

import pytest

from app.clients.coingecko import CoinGeckoError, MarketsResponse
from app.poller import Poller
from app.repository import RepositoryError


def make_poller(client=None, repo=None, interval=60):
    client = client or MagicMock()
    repo = repo or MagicMock()
    limiter = MagicMock()
    sleeps = []
    poller = Poller(client, repo, limiter, ("bitcoin", "ethereum", "solana"),
                    interval, sleep=sleeps.append)
    return poller, client, repo, limiter, sleeps


def item(coin, symbol, price):
    return {"id": coin, "symbol": symbol, "current_price": price,
            "total_volume": 1.0, "price_change_percentage_24h": 0.5}


def good_response():
    return MarketsResponse(
        data=[item("bitcoin", "btc", 100), item("ethereum", "eth", 50),
              item("solana", "sol", 5)],
        latency_ms=10.0,
    )


def test_poll_once_saves_every_coin():
    client = MagicMock()
    client.fetch_markets.return_value = good_response()
    poller, _, repo, _, _ = make_poller(client=client)

    assert poller.poll_once() == 3
    assert repo.save.call_count == 3


def test_non_retryable_error_is_attempted_once_and_returns_zero():
    client = MagicMock()
    client.fetch_markets.side_effect = CoinGeckoError("HTTP 400", retryable=False)
    poller, _, repo, _, sleeps = make_poller(client=client)

    assert poller.poll_once() == 0
    assert client.fetch_markets.call_count == 1
    assert sleeps == []
    repo.save.assert_not_called()


def test_retryable_error_is_retried_then_succeeds():
    client = MagicMock()
    client.fetch_markets.side_effect = [
        CoinGeckoError("HTTP 503", retryable=True),
        good_response(),
    ]
    poller, _, _, limiter, sleeps = make_poller(client=client)

    assert poller.poll_once() == 3
    assert client.fetch_markets.call_count == 2
    assert limiter.wait.call_count == 2   # every attempt is rate limited
    assert len(sleeps) == 1


def test_one_bad_coin_does_not_block_the_others():
    client = MagicMock()
    bad = MarketsResponse(
        data=[item("bitcoin", "btc", 100), item("ethereum", "eth", None),
              item("solana", "sol", 5)],
        latency_ms=10.0,
    )
    client.fetch_markets.return_value = bad
    poller, _, repo, _, _ = make_poller(client=client)

    assert poller.poll_once() == 2
    assert repo.save.call_count == 2


def test_repository_failure_skips_only_that_coin():
    client = MagicMock()
    client.fetch_markets.return_value = good_response()
    repo = MagicMock()
    repo.save.side_effect = [None, RepositoryError("db down"), None]
    poller, _, _, _, _ = make_poller(client=client, repo=repo)

    assert poller.poll_once() == 2


def test_all_coins_in_a_cycle_share_one_timestamp():
    client = MagicMock()
    client.fetch_markets.return_value = good_response()
    poller, _, repo, _, _ = make_poller(client=client)

    poller.poll_once()

    stamps = {call.args[0].polled_at for call in repo.save.call_args_list}
    assert len(stamps) == 1


def test_poll_failure_is_logged(caplog):
    client = MagicMock()
    client.fetch_markets.side_effect = CoinGeckoError("HTTP 400")
    poller, *_ = make_poller(client=client)

    with caplog.at_level("ERROR"):
        poller.poll_once()

    assert "Poll failed" in caplog.text