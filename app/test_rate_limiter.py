"""Tests for app.rate_limiter (fake clock, no real sleeping)."""

import pytest

from app.rate_limiter import RateLimiter


class FakeTime:
    """A controllable clock; sleeping just advances it."""

    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make(min_interval: float):
    fake = FakeTime()
    return RateLimiter(min_interval, clock=fake.clock, sleep=fake.sleep), fake


def test_first_call_never_waits():
    limiter, fake = make(2.0)
    assert limiter.wait() == 0.0
    assert fake.sleeps == []


def test_second_call_too_soon_sleeps_the_remainder():
    limiter, fake = make(2.0)
    limiter.wait()
    fake.now += 0.5
    assert limiter.wait() == pytest.approx(1.5)
    assert fake.sleeps == [pytest.approx(1.5)]


def test_call_after_interval_does_not_sleep():
    limiter, fake = make(2.0)
    limiter.wait()
    fake.now += 5.0
    assert limiter.wait() == 0.0
    assert fake.sleeps == []


def test_gap_is_measured_from_the_last_allowed_request():
    limiter, fake = make(2.0)
    limiter.wait()
    limiter.wait()   # sleeps 2.0, last_request is now t=102
    assert limiter.wait() == pytest.approx(2.0)


def test_negative_interval_rejected():
    with pytest.raises(ValueError):
        RateLimiter(-1)