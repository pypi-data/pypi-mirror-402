"""Tests for logging configuration helpers."""

import logging
from pathlib import Path

import pytest

from narrative_flow.logging_config import (
    LOG_FILE_ENV_VAR,
    LOG_LEVEL_ENV_VAR,
    LOG_PAYLOADS_ENV_VAR,
    configure_logging,
    resolve_log_level,
    resolve_log_payloads,
)


class TestResolveLogLevel:
    """Tests for resolve_log_level."""

    def test_defaults_to_info_when_no_inputs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Defaults to INFO when no env or CLI settings are provided."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

        assert resolve_log_level() == "INFO"

    def test_debug_flag_sets_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Debug flag yields DEBUG when no env override is present."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

        assert resolve_log_level(debug=True) == "DEBUG"

    def test_env_override_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variable overrides CLI and debug flags."""
        monkeypatch.setenv(LOG_LEVEL_ENV_VAR, "error")

        assert resolve_log_level(log_level="DEBUG", debug=True) == "ERROR"

    def test_warn_alias_is_supported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WARN aliases resolve to WARNING."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

        assert resolve_log_level(log_level="warn") == "WARNING"

    def test_invalid_level_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unknown log levels raise a ValueError."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

        with pytest.raises(ValueError):
            resolve_log_level(log_level="not-a-level")


class TestConfigureLogging:
    """Tests for configure_logging."""

    def test_configure_logging_returns_effective_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """configure_logging returns the effective level name."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)

        assert configure_logging(log_level="info").level == "INFO"

    def test_configure_logging_writes_to_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """configure_logging writes logs to the configured file."""
        monkeypatch.delenv(LOG_LEVEL_ENV_VAR, raising=False)
        log_file = tmp_path / "debug.log"
        settings = configure_logging(log_level="INFO", log_file=log_file)
        logger = logging.getLogger("narrative_flow.test")
        logger.info("hello log file")

        assert settings.log_file == log_file
        assert log_file.exists()
        assert "hello log file" in log_file.read_text()


class TestResolveLogPayloads:
    """Tests for resolve_log_payloads."""

    def test_defaults_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Payload logging defaults to False."""
        monkeypatch.delenv(LOG_PAYLOADS_ENV_VAR, raising=False)
        assert resolve_log_payloads() is False

    def test_env_override_enables_payloads(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variable enables payload logging."""
        monkeypatch.setenv(LOG_PAYLOADS_ENV_VAR, "true")
        assert resolve_log_payloads() is True


class TestResolveLogFile:
    """Tests for log file resolution."""

    def test_env_override_takes_precedence(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Environment variable overrides configured log file path."""
        env_log = tmp_path / "env.log"
        monkeypatch.setenv(LOG_FILE_ENV_VAR, str(env_log))

        settings = configure_logging(log_level="INFO", log_file=tmp_path / "cli.log")
        assert settings.log_file == env_log
