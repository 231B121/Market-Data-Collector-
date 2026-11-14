# Market Data Collector

Read-only service that collects crypto market data from the CoinGecko public API
and normalizes it into a standard schema. (Day 1: config, client, normalizer, logging, tests.)

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env

## Configuration (.env)

| Variable | Default | Notes |
|---|---|---|
| PAIRS | bitcoin,ethereum,solana | CoinGecko coin ids |
| POLL_INTERVAL_SECONDS | 60 | integer, 1-86400 |
| DB_URL | (required) | not used until Day 2 |
| LOG_LEVEL | info | debug/info/warning/error/critical |
| PORT | 8000 | 1-65535 |

Invalid or missing settings raise ConfigError listing every problem.

## Run tests

    pytest -v

Tests use mocks and make no live API calls.

## Data notes

- Source endpoint: /coins/markets (one batched request).
- CoinGecko's public API gives no bid/ask prices, so bid, ask, spread and
  spread_pct are null. The formulas are implemented and tested for when they exist.
- volume_24h and price_change_24h_pct are null if CoinGecko sends null.
