"""Structured logging with redaction support for SENTINAL."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional, Set

# Fields whose values are always redacted in log output
_REDACTED_FIELDS: Set[str] = {
    "password", "token", "secret", "api_key", "auth",
    "passphrase", "credential", "private_key",
}

_REDACT_PATTERN = re.compile(
    r"(" + "|".join(re.escape(f) for f in _REDACTED_FIELDS) + r")",
    re.IGNORECASE,
)


def _redact_value(key: str, value: Any) -> Any:
    """Return '[REDACTED]' if the key matches a sensitive field name."""
    if _REDACT_PATTERN.search(key):
        return "[REDACTED]"
    return value


def _redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *data* with sensitive values replaced."""
    return {k: _redact_value(k, v) for k, v in data.items()}


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: Dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "module": record.module,
            "msg": record.getMessage(),
        }
        # Attach extra contextual fields if present
        for key in ("operation", "duration_ms", "doc_id", "chunk_count"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = _redact_value(key, val)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class HumanFormatter(logging.Formatter):
    """Emit log records in a readable, coloured-ish format."""

    _LEVEL_SYMBOLS = {
        "DEBUG": "·",
        "INFO": "ℹ",
        "WARNING": "⚠",
        "ERROR": "✗",
        "CRITICAL": "☠",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        sym = self._LEVEL_SYMBOLS.get(record.levelname, "?")
        ts = self.formatTime(record, datefmt="%H:%M:%S")
        base = f"{ts} {sym} [{record.module}] {record.getMessage()}"
        extras = []
        for key in ("operation", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                extras.append(f"{key}={_redact_value(key, val)}")
        if extras:
            base += "  " + "  ".join(extras)
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def configure_logging(level: str = "INFO", fmt: str = "human") -> None:
    """Configure root logger for SENTINAL.

    Args:
        level: Standard Python log level string (e.g. "DEBUG", "INFO").
        fmt:   "json" or "human".
    """
    root = logging.getLogger("sentinal")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler()
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(HumanFormatter())
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'sentinal' namespace."""
    return logging.getLogger(f"sentinal.{name}")


class _Timer:
    """Context manager that records elapsed milliseconds."""

    def __init__(self) -> None:
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "_Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000


def timed_log(
    logger: logging.Logger,
    level: int,
    msg: str,
    operation: Optional[str] = None,
    **extra: Any,
) -> "_Timer":
    """Return a Timer context-manager that logs duration on exit.

    Usage::

        with timed_log(log, logging.INFO, "Indexed doc", operation="index"):
            ...
    """
    timer = _Timer()
    _orig_exit = timer.__exit__

    def _exit_and_log(*args: Any) -> None:
        _orig_exit(*args)
        fields: Dict[str, Any] = {"duration_ms": round(timer.elapsed_ms, 1)}
        if operation:
            fields["operation"] = operation
        fields.update(extra)
        logger.log(level, msg, extra=fields)

    timer.__exit__ = _exit_and_log  # type: ignore[method-assign]
    return timer
