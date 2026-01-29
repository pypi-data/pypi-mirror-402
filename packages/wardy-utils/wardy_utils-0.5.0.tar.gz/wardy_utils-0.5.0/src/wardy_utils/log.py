"""Set up logging using the Loguru library.

Requires the 'log' extra: pip install wardy-utils[log]
"""

from __future__ import annotations

import inspect
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

try:
    from loguru import logger
except ImportError as e:  # pragma: no cover
    msg = "loguru is required for wardy_utils.log. Install with: pip install wardy-utils[log]"
    raise ImportError(msg) from e

try:
    import logfire  # pyright: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    logfire = None


# ----- Settings -----


class LogSettings(BaseSettings):
    """Environment-driven settings for logging.

    Cascade behavior when not explicitly set:
    - logfire_service_name: Falls back to current working directory name.
    - logfire_environment: Falls back to APP_ENVIRONMENT, REFLEX_ENV_MODE,
                            NODE_ENV, ENVIRONMENT.
    """

    logfire_token: str | None = None
    logfire_service_name: str | None = None
    logfire_environment: str | None = None

    model_config = SettingsConfigDict(env_prefix="WARDY_UTILS_LOG_", case_sensitive=False)

    @field_validator("logfire_service_name")
    @classmethod
    def cascade_service_name(cls, v: str | None) -> str:
        """Fall back to current working directory name if not explicitly set."""
        return v or Path.cwd().name

    @field_validator("logfire_environment")
    @classmethod
    def cascade_environment(cls, v: str | None) -> str | None:
        """Fall back to common environment variables if not explicitly set."""
        return (
            v
            or os.getenv("APP_ENVIRONMENT")
            or os.getenv("REFLEX_ENV_MODE")
            or os.getenv("NODE_ENV")
            or os.getenv("ENVIRONMENT")
        )


# ----- Config -----


@dataclass
class LogConfig:
    """Configuration for log formats and rotation."""

    stderr_level = "WARNING"
    file_log_level = "DEBUG"
    standard_format: str = "[{time:HH:mm:ss}] {level} - {message}"
    detail_format: str = "{time} {file:>25}:{line:<4} {level:<8} {message}"
    rotation: str = "1 hour"
    retention: str = "7 days"


# ----- Public API -----

__all__ = ["LogConfig", "LogSettings", "configure_logfire", "configure_logging", "logger"]


def configure_logging(
    log_filename: str | Path,
    *,
    service_name: str | None = None,
    environment: str | None = None,
    config: LogConfig | None = None,
) -> None:
    """Setup Loguru logging for the application.

    Args:
        log_filename: Base name for the log file (will have .log suffix added).
        service_name: Service name for Logfire cloud logging. Required if using Logfire.
        environment: Environment name for Logfire (e.g. 'dev', 'staging', 'prod').
        config: Optional LogConfig for customizing formats and rotation.

    Environment variables (prefix WARDY_UTILS_LOG_):
        LOGFIRE_TOKEN: Token for Logfire cloud logging.
        LOGFIRE_SERVICE_NAME: Service name for Logfire.
        LOGFIRE_ENVIRONMENT: Environment name for Logfire.
    """
    settings = LogSettings()
    config = config or LogConfig()

    # Capture things like Hishel logging
    intercept_logging()

    # Replace the default StdErr handler.
    logger.remove()
    logger.add(sys.stderr, level=config.stderr_level, format=config.standard_format)

    # Add a rotating file handler.
    log_filename = Path(log_filename).with_suffix(".log")
    logger.add(
        log_filename,
        level=config.file_log_level,
        format=config.detail_format,
        rotation=config.rotation,
        retention=config.retention,
    )

    # Set up Logfire if token is configured
    if settings.logfire_token:
        svc = service_name or settings.logfire_service_name
        env = environment or settings.logfire_environment
        configure_logfire(
            settings.logfire_token,
            service_name=svc,
            log_format=config.detail_format,
            environment=env,
        )


def configure_logfire(
    token: str, *, service_name: str | None, log_format: str, environment: str | None = None
) -> None:
    """Configure Logfire cloud logging with available instrumentations.

    Args:
        token: Logfire API token.
        service_name: Service name for Logfire. Required.
        log_format: Log format string for Logfire handler.
        environment: Environment name for Logfire (e.g. 'dev', 'prod'). Optional.

    Raises:
        ImportError: If logfire is not installed.
        ValueError: If service_name is not provided.
    """
    if logfire is None:
        msg = "logfire is required for cloud logging. Install with: pip install logfire"
        raise ImportError(msg)

    if not service_name:
        msg = "service_name is required for Logfire"
        raise ValueError(msg)

    if environment:
        logfire.configure(token=token, service_name=service_name, environment=environment)
    else:
        logfire.configure(token=token, service_name=service_name)

    logger.add(logfire.loguru_handler()["sink"], level="TRACE", format=log_format)

    # Instrument available integrations
    _try_instrument("system_metrics", logfire.instrument_system_metrics)
    _try_instrument("psycopg", logfire.instrument_psycopg)
    _try_instrument("httpx", logfire.instrument_httpx)
    _try_instrument("sqlalchemy", logfire.instrument_sqlalchemy)
    _try_instrument("redis", logfire.instrument_redis)
    _try_instrument("asyncpg", logfire.instrument_asyncpg)


def _try_instrument(name: str, func: Callable[[], None]) -> None:
    """Try to instrument a library, logging the result."""
    try:
        func()
    except RuntimeError:
        logger.debug(f"Logfire: {name} not available")
    else:
        logger.debug(f"Logfire: instrumented {name}")


# ----- Interface to the standard logging module -----


class InterceptHandler(logging.Handler):
    """Send logs to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:  # pragma: no cover
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def intercept_logging() -> None:
    """Intercept standard logging and send it to Loguru."""
    # Configure the root logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
