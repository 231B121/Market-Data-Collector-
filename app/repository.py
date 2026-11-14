"""Database access for MarketRecord (PostgreSQL via psycopg 3)."""

import logging
from dataclasses import asdict

import psycopg
from psycopg.rows import dict_row

from app.models import MarketRecord

logger = logging.getLogger(__name__)

COLUMNS = (
    "symbol, exchange, price, bid, ask, spread, spread_pct, volume_24h, "
    "price_change_24h_pct, api_latency_ms, polled_at, raw_response_id"
)

INSERT_SQL = """
INSERT INTO market_records (
    symbol, exchange, price, bid, ask, spread, spread_pct, volume_24h,
    price_change_24h_pct, api_latency_ms, polled_at, raw_response_id
) VALUES (
    %(symbol)s, %(exchange)s, %(price)s, %(bid)s, %(ask)s, %(spread)s,
    %(spread_pct)s, %(volume_24h)s, %(price_change_24h_pct)s,
    %(api_latency_ms)s, %(polled_at)s, %(raw_response_id)s
)
"""

SELECT_LATEST_SQL = f"""
SELECT {COLUMNS} FROM market_records
WHERE symbol = %s
ORDER BY polled_at DESC
LIMIT %s
"""


class RepositoryError(Exception):
    """Raised when a database operation fails."""


class MarketRepository:
    """Saves and reads MarketRecord rows. Contains all the SQL."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url

    def save(self, record: MarketRecord) -> None:
        """Insert one record. Raises RepositoryError on failure."""
        try:
            with psycopg.connect(self._db_url) as conn:
                conn.execute(INSERT_SQL, asdict(record))
        except psycopg.Error as exc:
            raise RepositoryError(f"Could not save record: {exc}") from exc

    def get_latest(self, symbol: str, limit: int = 10) -> list[dict]:
        """Return the newest records for a symbol, newest first."""
        try:
            with psycopg.connect(self._db_url, row_factory=dict_row) as conn:
                return conn.execute(SELECT_LATEST_SQL, (symbol, limit)).fetchall()
        except psycopg.Error as exc:
            raise RepositoryError(f"Could not read records: {exc}") from exc