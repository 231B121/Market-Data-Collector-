"""Tests for application configuration."""

import pytest

from app.config import ConfigError, Settings, load_settings


def test_load_settings_success():
    env = {
        "DB_URL": "postgresql://test:test@localhost:5432/testdb",
        "PAIRS": "bitcoin,ethereum,solana",
        "POLL_INTERVAL_SECONDS": "30",
        "LOG_LEVEL": "debug",
        "PORT": "9000",
    }
    settings = load_settings(env)
    assert isinstance(settings, Settings)
    assert settings.pairs == ("bitcoin", "ethereum", "solana")
    assert settings.poll_interval_seconds == 30
    assert settings.log_level == "debug"
    assert settings.port == 9000
    assert settings.db_url == "postgresql://test:test@localhost:5432/testdb"


def test_load_settings_defaults():
    env = {
        "DB_URL": "postgresql://test:test@localhost:5432/testdb",
    }
    settings = load_settings(env)
    assert settings.pairs == ("bitcoin", "ethereum", "solana")
    assert settings.poll_interval_seconds == 60
    assert settings.log_level == "info"
    assert settings.port == 8000


def test_load_settings_missing_db_url():
    with pytest.raises(ConfigError) as exc_info:
        load_settings({})
    assert "DB_URL is required" in str(exc_info.value)


def test_load_settings_invalid_log_level():
    env = {
        "DB_URL": "postgresql://test:test@localhost:5432/testdb",
        "LOG_LEVEL": "invalid_level",
    }
    with pytest.raises(ConfigError) as exc_info:
        load_settings(env)
    assert "LOG_LEVEL must be one of" in str(exc_info.value)


def test_load_settings_invalid_integers():
    env = {
        "DB_URL": "postgresql://test:test@localhost:5432/testdb",
        "POLL_INTERVAL_SECONDS": "not_an_int",
        "PORT": "70000",
    }
    with pytest.raises(ConfigError) as exc_info:
        load_settings(env)
    assert "POLL_INTERVAL_SECONDS must be an integer" in str(exc_info.value)
    assert "PORT must be between 1 and 65535" in str(exc_info.value)


def test_load_settings_empty_pairs():
    env = {
        "DB_URL": "postgresql://test:test@localhost:5432/testdb",
        "PAIRS": "  ,  ",
    }
    with pytest.raises(ConfigError) as exc_info:
        load_settings(env)
    assert "PAIRS must contain at least one coin id" in str(exc_info.value)
