"""Public-safe artifact schemas for the Vercel showcase."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PublicArtifact(BaseModel):
    """JSON envelope required for every public showcase artifact."""

    schema_version: str = "1.0"
    generated_at: str
    data_mode: str = "public_demo"
    source_categories: list[str]
    lineage: list[dict[str, Any]] = Field(default_factory=list)
    synthetic_flag: bool = True
    caveats: list[str] = Field(default_factory=list)
    payload: Any


class ActionInterpretation(BaseModel):
    """Deterministic interpretation block attached to scenarios and forecasts."""

    what_changed: str
    why_it_changed: str
    confidence: str
    improved: list[str] = Field(default_factory=list)
    worsened: list[str] = Field(default_factory=list)
    bottleneck_moved_to: str
    watch_points: list[str]
    operational_levers: list[str]
    validation_needed: list[str]
    limitations: list[str]
    huddle_brief: list[str]
