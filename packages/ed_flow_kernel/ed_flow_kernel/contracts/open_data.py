"""Open-data and public-synthetic source contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OpenDataContract(BaseModel):
    """Source metadata required by both Snowflake and public exports."""

    source_id: str
    display_name: str
    source_family: str
    category: str
    grain: str = "source-defined"
    geography: str = "source-defined"
    expected_refresh_minutes: int | None = None
    snowflake_target: str | None = None
    public_safe: bool = True
    caveats: list[str] = Field(default_factory=list)
