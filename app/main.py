"""Entry point: wire the components together and run the poller."""

import logging
import sys

from app.clients.coingecko import CoinGeckoClient
from app.config import ConfigError, load_settings
from app.logging_config import setup_logging
from app.poller import Poller
from app.rate_limiter import RateLimiter
from app.repository import MarketRepository

# Minimum seconds between CoinGecko requests (public API is rate limited).
MIN_REQUEST_INTERVAL_SECONDS = 2.0


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as exc:
        # Logging isn't configured yet, so write the error to stderr directly.
        sys.stderr.write(f"{exc}\n")
        return 1

    setup_logging(settings.log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # quiet library noise
    logger = logging.getLogger(__name__)

    client = CoinGeckoClient()
    poller = Poller(
        client=client,
        repository=MarketRepository(settings.db_url),
        rate_limiter=RateLimiter(MIN_REQUEST_INTERVAL_SECONDS),
        pairs=settings.pairs,
        interval_seconds=settings.poll_interval_seconds,
    )

    try:
        poller.run_forever()
    except Exception:
        logger.exception("Poller crashed")
        return 1
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())