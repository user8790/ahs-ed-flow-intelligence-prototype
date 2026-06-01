"""Snowflake backend factory with guarded imports and local fallback."""

from __future__ import annotations

from ed_flow.config import AppConfig
from ed_flow.snowflake_backend import SnowflakeBackend, fallback_connection_environment_notes


def create_snowflake_backend(config: AppConfig | None = None, fallback_to_local: bool = True) -> SnowflakeBackend:
    """Return the existing guarded Snowflake backend."""

    return SnowflakeBackend(config or AppConfig.from_env(), fallback_to_local=fallback_to_local)


def snowflake_environment_notes() -> dict[str, str]:
    """Expose safe environment variable names without printing secrets."""

    return fallback_connection_environment_notes()
