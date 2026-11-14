"""Client-side rate limiting: enforce a minimum gap between requests."""

import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class RateLimiter:
    """Blocks so that calls to wait() are at least min_interval seconds apart.

    Not thread-safe: intended for a single polling loop.
    """

    def __init__(
        self,
        min_interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if min_interval < 0:
            raise ValueError("min_interval must be >= 0")
        self._min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last_request: float | None = None

    def wait(self) -> float:
        """Sleep if needed, then record this request. Returns seconds slept."""
        waited = 0.0
        now = self._clock()
        if self._last_request is not None:
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                waited = self._min_interval - elapsed
                logger.debug("Rate limit: sleeping %.2fs", waited)
                self._sleep(waited)
        self._last_request = self._clock()
        return waited