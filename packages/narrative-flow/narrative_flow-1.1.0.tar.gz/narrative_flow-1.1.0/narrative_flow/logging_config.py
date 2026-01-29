"""Logging configuration helpers for narrative_flow."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

LOG_LEVEL_ENV_VAR: Final = "NARRATIVE_FLOW_LOG_LEVEL"
LOG_PAYLOADS_ENV_VAR: Final = "NARRATIVE_FLOW_LOG_PAYLOADS"
LOG_FILE_ENV_VAR: Final = "NARRATIVE_FLOW_LOG_FILE"
LOG_PAYLOAD_MAX_CHARS_ENV_VAR: Final = "NARRATIVE_FLOW_LOG_PAYLOAD_MAX_CHARS"

DEFAULT_PAYLOAD_MAX_CHARS: Final = 2000
DEFAULT_REDACTIONS: Final = (
    (re.compile(r"(?i)(api[_-]?key\\s*[:=]\\s*)([^\\s'\\\"]+)"), r"\\1***REDACTED***"),
    (re.compile(r"(?i)(authorization\\s*[:=]\\s*bearer\\s+)([A-Za-z0-9._-]+)"), r"\\1***REDACTED***"),
    (re.compile(r"\\bsk-[A-Za-z0-9]{16,}\\b"), "sk-***REDACTED***"),
    (re.compile(r"\\brk-[A-Za-z0-9]{16,}\\b"), "rk-***REDACTED***"),
)

_LOG_LEVELS: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
    "FATAL": logging.CRITICAL,
    "WARN": logging.WARNING,
}


@dataclass(frozen=True)
class LoggingSettings:
    """Resolved logging settings for narrative_flow."""

    level: str
    log_payloads: bool
    payload_max_chars: int
    redactions: tuple[tuple[re.Pattern[str], str], ...]
    log_file: Path | None


def resolve_log_level(log_level: str | None = None, debug: bool = False) -> str:
    """Resolve the effective log level name.

    Args:
        log_level: Optional log level name from CLI or caller.
        debug: Whether to enable debug logging when no level is provided.

    Returns:
        The normalized log level name.

    Raises:
        ValueError: If the log level is not recognized.
    """
    env_level = os.environ.get(LOG_LEVEL_ENV_VAR)
    candidate = env_level or log_level
    if candidate is None or not str(candidate).strip():
        candidate = "DEBUG" if debug else "INFO"

    normalized = str(candidate).strip().upper()
    if normalized not in _LOG_LEVELS:
        allowed = ", ".join(sorted({level for level in _LOG_LEVELS if level.isalpha()}))
        raise ValueError(f"Invalid log level '{candidate}'. Expected one of: {allowed}")

    if normalized == "WARN":
        return "WARNING"
    if normalized == "FATAL":
        return "CRITICAL"
    return normalized


def resolve_log_payloads(log_payloads: bool | None = None) -> bool:
    """Resolve whether payload logging is enabled.

    Args:
        log_payloads: Optional payload logging flag.

    Returns:
        True if payload logging is enabled, otherwise False.
    """
    env_value = os.environ.get(LOG_PAYLOADS_ENV_VAR)
    if env_value is not None:
        normalized = env_value.strip().lower()
        return normalized in {"1", "true", "yes", "on"}
    return bool(log_payloads)


def resolve_log_payload_max_chars(payload_max_chars: int | None = None) -> int:
    """Resolve the max character count for payload logging.

    Args:
        payload_max_chars: Optional maximum payload size.

    Returns:
        Max characters to log per payload.
    """
    env_value = os.environ.get(LOG_PAYLOAD_MAX_CHARS_ENV_VAR)
    if env_value is not None and env_value.strip():
        try:
            value = int(env_value.strip())
        except ValueError:
            return DEFAULT_PAYLOAD_MAX_CHARS
        return max(value, 0)
    if payload_max_chars is None:
        return DEFAULT_PAYLOAD_MAX_CHARS
    return max(payload_max_chars, 0)


def resolve_log_file(log_file: str | Path | None = None) -> Path | None:
    """Resolve the log file path.

    Args:
        log_file: Optional log file path.

    Returns:
        Path to the log file or None.
    """
    env_value = os.environ.get(LOG_FILE_ENV_VAR)
    candidate = env_value if env_value is not None and env_value.strip() else log_file
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return None
    return Path(candidate).expanduser()


_SETTINGS = LoggingSettings(
    level=resolve_log_level(),
    log_payloads=resolve_log_payloads(),
    payload_max_chars=resolve_log_payload_max_chars(),
    redactions=DEFAULT_REDACTIONS,
    log_file=resolve_log_file(),
)


def configure_logging(
    log_level: str | None = None,
    debug: bool = False,
    log_file: str | Path | None = None,
    log_payloads: bool | None = None,
    payload_max_chars: int | None = None,
    redactions: tuple[tuple[re.Pattern[str], str], ...] | None = None,
) -> LoggingSettings:
    """Configure standard logging for narrative_flow.

    Args:
        log_level: Optional log level name from CLI or caller.
        debug: Whether to enable debug logging when no level is provided.
        log_file: Optional log file path for debug output.
        log_payloads: Whether to log prompts and responses (redacted, truncated).
        payload_max_chars: Max characters to log per payload.
        redactions: Optional redaction patterns (regex, replacement).

    Returns:
        The resolved logging settings.

    Raises:
        ValueError: If the log level is not recognized.
    """
    effective_level = resolve_log_level(log_level=log_level, debug=debug)
    effective_payloads = resolve_log_payloads(log_payloads=log_payloads)
    effective_payload_max_chars = resolve_log_payload_max_chars(payload_max_chars=payload_max_chars)
    effective_redactions = redactions or DEFAULT_REDACTIONS
    effective_log_file = resolve_log_file(log_file=log_file)

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if effective_log_file is not None:
        effective_log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(effective_log_file, encoding="utf-8"))

    logging.basicConfig(
        level=_LOG_LEVELS[effective_level],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )

    global _SETTINGS
    _SETTINGS = LoggingSettings(
        level=effective_level,
        log_payloads=effective_payloads,
        payload_max_chars=effective_payload_max_chars,
        redactions=effective_redactions,
        log_file=effective_log_file,
    )
    return _SETTINGS


def should_log_payloads() -> bool:
    """Return whether payload logging is enabled."""
    return _SETTINGS.log_payloads


def format_payload(value: str) -> str:
    """Redact and truncate payload values for logging.

    Args:
        value: Raw payload content.

    Returns:
        Sanitized payload content.
    """
    sanitized = value
    for pattern, replacement in _SETTINGS.redactions:
        sanitized = pattern.sub(replacement, sanitized)
    if _SETTINGS.payload_max_chars <= 0:
        return "... [truncated]"
    if len(sanitized) > _SETTINGS.payload_max_chars:
        return f"{sanitized[: _SETTINGS.payload_max_chars]}... [truncated]"
    return sanitized


def format_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Format message payloads for logging.

    Args:
        messages: Message dictionaries with role/content.

    Returns:
        Sanitized message payloads.
    """
    formatted = []
    for message in messages:
        formatted.append({
            "role": message.get("role", ""),
            "content": format_payload(message.get("content", "")),
        })
    return formatted
