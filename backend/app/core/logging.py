"""Structured application logging with sensitive-data redaction."""

import logging
import re
import sys
from typing import Any

SENSITIVE_PATTERNS = [
    (re.compile(r"(password|passwd|secret|token|authorization|cookie|api[_-]?key)"
                r"\s*[=:]\s*['\"]?[^\s'\"]+", re.IGNORECASE), r"\1=[REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED]"),
]


class RedactingFilter(logging.Filter):
    """Filter that redacts secrets from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_value(a) for a in record.args)
        return True


def redact_sensitive(text: str) -> str:
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive(value)
    return value


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with redaction filter."""
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(RedactingFilter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
