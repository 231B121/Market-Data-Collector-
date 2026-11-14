CREATE TABLE IF NOT EXISTS market_records (
    id                    BIGSERIAL PRIMARY KEY,
    symbol                TEXT             NOT NULL,
    exchange              TEXT             NOT NULL,
    price                 DOUBLE PRECISION NOT NULL,
    bid                   DOUBLE PRECISION,
    ask                   DOUBLE PRECISION,
    spread                DOUBLE PRECISION,
    spread_pct            DOUBLE PRECISION,
    volume_24h            DOUBLE PRECISION,
    price_change_24h_pct  DOUBLE PRECISION,
    api_latency_ms        DOUBLE PRECISION NOT NULL,
    polled_at             TIMESTAMPTZ      NOT NULL,
    raw_response_id       TEXT
);

CREATE INDEX IF NOT EXISTS idx_market_records_symbol_polled_at
    ON market_records (symbol, polled_at DESC);
