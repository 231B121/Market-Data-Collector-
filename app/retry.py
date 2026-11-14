"""Retry with exponential backoff."""

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def backoff_delay(
    attempt: int, base: float = 1.0, cap: float = 60.0, jitter: float = 0.0
) -> float:
    """Seconds to wait after failed attempt number `attempt` (1-based)."""
    delay = min(cap, base * 2 ** (attempt - 1))
    if jitter:
        delay += random.uniform(0, jitter * delay)
    return delay


def retry(
    func: Callable[[], T],
    *,
    max_attempts: int = 4,
    base: float = 1.0,
    cap: float = 60.0,
    jitter: float = 0.1,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    should_retry: Callable[[Exception], bool] = lambda exc: True,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call func(); on a retryable failure wait and try again."""
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except retry_on as exc:
            if attempt == max_attempts or not should_retry(exc):
                raise
            delay = backoff_delay(attempt, base, cap, jitter)
            logger.warning(
                "Attempt %d/%d failed (%s); retrying in %.1fs",
                attempt, max_attempts, exc, delay,
            )
            sleep(delay)
    raise RuntimeError("unreachable")  # keeps type checkers happy