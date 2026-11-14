"""Tests for app.config."""

import pytest

from app.config import ConfigError, load_settings


def test_defaults_are_applied(valid_env):
    settings = load_settings(valid_env)

    assert settings.pairs == ("bitcoin", "ethereum", "solana")
    assert settings.poll_interval_seconds == 60
    assert settings.log_level == "info"
    assert settings.port == 8000


def test_pairs_are_trimmed_lowercased_and_empties_dropped(valid_env):
    valid_env["PAIRS"] = " Bitcoin , ETHEREUM ,, "
    assert load_settings(valid_env).pairs == ("bitcoin", "ethereum")


def test_missing_db_url_raises():
    with pytest.raises(ConfigError, match="DB_URL"):
        load_settings({})


def test_blank_db_url_raises():
    with pytest.raises(ConfigError, match="DB_URL"):
        load_settings({"DB_URL": "   "})


def test_non_integer_port_raises(valid_env):
    valid_env["PORT"] = "abc"
    with pytest.raises(ConfigError, match="PORT"):
        load_settings(valid_env)


def test_out_of_range_port_raises(valid_env):
    valid_env["PORT"] = "70000"
    with pytest.raises(ConfigError, match="PORT"):
        load_settings(valid_env)


def test_invalid_log_level_raises(valid_env):
    valid_env["LOG_LEVEL"] = "loud"
    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        load_settings(valid_env)


def test_all_errors_are_reported_together():
    with pytest.raises(ConfigError) as exc_info:
        load_settings({"PORT": "abc", "LOG_LEVEL": "loud"})

    message = str(exc_info.value)
    assert "PORT" in message
    assert "LOG_LEVEL" in message
    assert "DB_URL" in message


def test_empty_interval_uses_default(valid_env):
    valid_env["POLL_INTERVAL_SECONDS"] = ""
    assert load_settings(valid_env).poll_interval_seconds == 60