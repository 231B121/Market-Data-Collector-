"""Application configuration loaded from environment variables."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from dotenv import load_dotenv

VALID_LOG_LEVELS = {"debug", "info", "warning", "error", "critical"}


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Validated, read-only application settings."""

    pairs: tuple[str, ...]
    poll_interval_seconds: int
    db_url: str = field(repr=False)  # hidden from printouts: may hold a password
    log_level: str
    port: int


def _parse_int(
    env: Mapping[str, str],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
    errors: list[str],
) -> int:
    """Read an integer setting; record an error if it is invalid."""
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{name} must be an integer, got {raw!r}")
        return default
    if not minimum <= value <= maximum:
        errors.append(f"{name} must be between {minimum} and {maximum}, got {value}")
    return value


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Load and validate settings.

    If env is None, read .env (if present) and the real environment.
    Passing a dict lets tests supply their own values.
    """
    if env is None:
        load_dotenv()
        env = os.environ

    errors: list[str] = []

    pairs_raw = env.get("PAIRS", "bitcoin,ethereum,solana")
    pairs = tuple(p.strip().lower() for p in pairs_raw.split(",") if p.strip())
    if not pairs:
        errors.append("PAIRS must contain at least one coin id, e.g. bitcoin,ethereum")

    poll_interval = _parse_int(env, "POLL_INTERVAL_SECONDS", 60, 1, 86400, errors)
    port = _parse_int(env, "PORT", 8000, 1, 65535, errors)

    log_level = env.get("LOG_LEVEL", "info").strip().lower()
    if log_level not in VALID_LOG_LEVELS:
        errors.append(
            f"LOG_LEVEL must be one of {sorted(VALID_LOG_LEVELS)}, got {log_level!r}"
        )

    db_url = env.get("DB_URL", "").strip()
    if not db_url:
        errors.append("DB_URL is required but missing or empty")

    if errors:
        details = "\n".join(f"  - {e}" for e in errors)
        raise ConfigError(f"Invalid configuration:\n{details}")

    return Settings(
        pairs=pairs,
        poll_interval_seconds=poll_interval,
        db_url=db_url,
        log_level=log_level,
        port=port,
    )