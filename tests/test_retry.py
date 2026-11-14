"""Tests for app.retry (no real sleeping)."""

import pytest

from app.retry import backoff_delay, retry


def test_backoff_doubles_until_cap():
    assert [backoff_delay(a) for a in (1, 2, 3, 4, 5)] == [1, 2, 4, 8, 16]
    assert backoff_delay(10, cap=30) == 30


def test_jitter_stays_within_bounds():
    for _ in range(100):
        assert 4 <= backoff_delay(3, jitter=0.5) <= 6


def test_succeeds_after_failures_and_sleeps_between():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("temporary")
        return "ok"

    result = retry(flaky, jitter=0, sleep=sleeps.append)

    assert result == "ok"
    assert len(calls) == 3
    assert sleeps == [1, 2]


def test_gives_up_after_max_attempts():
    sleeps = []

    def always_fails():
        raise ValueError("down")

    with pytest.raises(ValueError):
        retry(always_fails, max_attempts=3, jitter=0, sleep=sleeps.append)
    assert len(sleeps) == 2  # no sleep after the final attempt


def test_non_retryable_error_is_raised_immediately():
    sleeps = []

    def bad_request():
        raise ValueError("400")

    with pytest.raises(ValueError):
        retry(bad_request, should_retry=lambda e: False, sleep=sleeps.append)
    assert sleeps == []