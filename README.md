# Market Data Collector

A resilient crypto market data collection service designed to poll public exchange endpoints, normalize payload records into consistent domain schemas, and provide structured observability and error handling.

## Features Built (Day 1 WIP)

- **Configuration Management (`app/config.py`)**:
  - Environment-based settings powered by `python-dotenv`.
  - Type-safe, validated, and immutable `Settings` dataclass.
  - Safe representation hiding sensitive fields (`db_url`).
- **Data Models (`app/models.py`)**:
  - Strongly typed `MarketRecord` schema representing coin snapshots.
  - Formatted serialization (`to_dict`) with ISO 8601 UTC timestamps.
- **CoinGecko Integration (`app/clients/coingecko.py`)**:
  - Public REST client fetching market snapshots in batch.
  - Round-trip latency tracking (`api_latency_ms`).
  - Robust exception hierarchy handling network timeouts, rate limits, and invalid formats.
- **Data Normalizer (`app/services/normalizer.py`)**:
  - Maps external exchange payloads to standard domain models (`MarketRecord`).
  - Calculates spreads and spread percentages.
  - Validates required fields and logs missing requested pairs.
- **Structured Logging (`app/logging_config.py`)**:
  - Consistent ISO-UTC timestamped key-value log formatter.
  - Dynamic attachment of structured context (`symbol`, `api_latency_ms`).
- **Unit Test Suite (`tests/`)**:
  - 100% passing pytest suite covering configuration parsing, normalization, spread math, logging formatters, and mocked CoinGecko API client interactions.

## Project Structure

```text
market-data-collector/
├── app/
│   ├── clients/
│   │   ├── __init__.py
│   │   └── coingecko.py       # CoinGecko REST client
│   ├── services/
│   │   ├── __init__.py
│   │   └── normalizer.py      # Normalization and spread computation
│   ├── __init__.py
│   ├── config.py              # Settings and environment validation
│   ├── logging_config.py      # Structured key-value logging
│   └── models.py              # Domain dataclasses (MarketRecord)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Test configurations
│   ├── test_coingecko.py      # Client tests (mocked HTTP)
│   ├── test_config.py         # Config validation tests
│   ├── test_logging.py        # Key-value formatter tests
│   └── test_normalizer.py     # Normalization & spread tests
├── .env.example               # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure variables as needed:

```bash
cp .env.example .env
```

Available configuration options:
- `DB_URL`: PostgreSQL connection string (required).
- `PAIRS`: Comma-separated CoinGecko coin identifiers (default: `bitcoin,ethereum,solana`).
- `POLL_INTERVAL_SECONDS`: Interval in seconds between market polls (default: `60`).
- `LOG_LEVEL`: Log level (`debug`, `info`, `warning`, `error`, `critical`) (default: `info`).
- `PORT`: Service port (default: `8000`).

### 3. Running Unit Tests

Run test suite with pytest:

```bash
pytest -v
```
