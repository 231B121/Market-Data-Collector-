"""Tests for logging configuration and KeyValueFormatter."""

import logging

from app.logging_config import KeyValueFormatter, setup_logging


def test_key_value_formatter():
    formatter = KeyValueFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Test message with \"quotes\"",
        args=(),
        exc_info=None,
    )
    record.symbol = "ETH-USD"
    record.api_latency_ms = 45.2

    output = formatter.format(record)
    assert "level=INFO" in output
    assert "component=test_logger" in output
    assert "message=\"Test message with 'quotes'\"" in output
    assert "symbol=ETH-USD" in output
    assert "api_latency_ms=45.2" in output


def test_setup_logging():
    setup_logging("debug")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
