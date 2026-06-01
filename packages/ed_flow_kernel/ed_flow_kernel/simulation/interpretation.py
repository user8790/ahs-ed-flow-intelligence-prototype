"""Deterministic action interpretation helpers."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.operational_intelligence import deterministic_huddle_brief, pressure_to_action_translator, scenario_impact_cards


def action_huddle(title: str, impact: pd.DataFrame, watchpoints: list[str], levers: list[str], confidence: str = "moderate") -> list[str]:
    """Return a five-line huddle brief."""

    return deterministic_huddle_brief(title, impact, watchpoints, levers, confidence)


__all__ = ["action_huddle", "pressure_to_action_translator", "scenario_impact_cards"]
