"""Logging setup: one consistent format for the whole service."""

import logging
import sys
from datetime import datetime, timezone

# Optional fields that polling logs may attach via extra={...}
EXTRA_FIELDS = ("symbol", "api_latency_ms")


class KeyValueFormatter(logging.Formatter):
    """Format records as: <ISO-UTC time> level=... component=... message="..." """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(
            timespec="milliseconds"
        )
        message = record.getMessage().replace('"', "'")
        parts = [
            timestamp,
            f"level={record.levelname}",
            f"component={record.name}",
            f'message="{message}"',
        ]
        for field in EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                parts.append(f"{field}={value}")
        line = " ".join(parts)
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def setup_logging(level: str = "info") -> None:
    """Configure the root logger. Call once at startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(KeyValueFormatter())

    root = logging.getLogger()
    root.handlers.clear()  # avoid duplicate lines if called twice
    root.addHandler(handler)
    root.setLevel(level.upper())