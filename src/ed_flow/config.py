"""Configuration helpers for local and Snowflake execution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


class AppConfig(BaseModel):
    """Runtime configuration without requiring pydantic-settings."""

    backend_mode: Literal["local", "snowflake"] = Field(default="local")
    model_provider: Literal["mock", "openai", "snowflake", "none"] = Field(default="mock")
    data_dir: Path = Field(default=DEFAULT_DATA_DIR)
    default_facility: str = Field(default="Stollery Children's Hospital")
    default_pediatric_only: bool = Field(default=True)
    snowflake_database: str = Field(
        default="DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS"
    )
    snowflake_schema: str = Field(default="MSB_CLINICAL_GENETICS")
    snowflake_warehouse: str = Field(default="WH_SMALL")
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4.1-mini")

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build config from environment variables with safe local defaults."""

        return cls(
            backend_mode=os.getenv("ED_FLOW_BACKEND", "local").lower(),
            model_provider=os.getenv("ED_FLOW_MODEL_PROVIDER", "mock").lower(),
            data_dir=Path(os.getenv("ED_FLOW_SYNTHETIC_DATA_DIR", str(DEFAULT_DATA_DIR))),
            default_facility=os.getenv(
                "ED_FLOW_DEFAULT_FACILITY", "Stollery Children's Hospital"
            ),
            default_pediatric_only=os.getenv("ED_FLOW_DEFAULT_PEDIATRIC_ONLY", "true")
            .strip()
            .lower()
            in {"1", "true", "yes", "y"},
            snowflake_database=os.getenv(
                "SNOWFLAKE_DATABASE",
                "DB_TEAM_STOLLERY_AND_ALBERTA_CHILDRENS_HOSPITAL_ANALYTICS",
            ),
            snowflake_schema=os.getenv("SNOWFLAKE_SCHEMA", "MSB_CLINICAL_GENETICS"),
            snowflake_warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_SMALL"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )


def get_config() -> AppConfig:
    """Return the active application configuration."""

    return AppConfig.from_env()

