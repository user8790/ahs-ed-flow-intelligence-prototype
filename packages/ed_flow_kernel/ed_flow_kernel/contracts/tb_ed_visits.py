"""TB_ED_VISITS contract and safe constrained projections."""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, Field

from ed_flow.data_contracts import (
    CONSTRAINED_ANALYSIS_COLUMNS,
    SENSITIVE_COLUMNS,
    SNOWFLAKE_SELECT_COLUMNS,
    TB_ED_VISITS_COLUMNS,
)


class TbEdVisitsContract(BaseModel):
    """Portable metadata for the curated ED/UCC/AACC visit table."""

    table_name: str = "TB_ED_VISITS"
    grain: str = "one row per ED/UCC/AACC visit"
    primary_key: str = "DATA_RECORD_ID"
    primary_start_timestamp: str = "FIRST_CONTACT_DATETIME"
    required_columns: list[str] = Field(default_factory=lambda: list(TB_ED_VISITS_COLUMNS))
    snowflake_select_columns: list[str] = Field(default_factory=lambda: list(SNOWFLAKE_SELECT_COLUMNS))
    sensitive_columns: list[str] = Field(default_factory=lambda: sorted(SENSITIVE_COLUMNS))
    default_rules: list[str] = Field(
        default_factory=lambda: [
            "Exclude INVALID_LOS_CALC_FLAG = 'Y' for LOS analysis.",
            "Exclude scheduled ED visits by default for typical walk-in ED analysis.",
            "Use FIRST_CONTACT_DATETIME as the primary visit start timestamp.",
            "Do not use ROW_CREATE_DATETIME or ROW_UPDATE_DATETIME as clinical event timestamps.",
        ]
    )

    @property
    def constrained_columns(self) -> list[str]:
        return list(CONSTRAINED_ANALYSIS_COLUMNS)


def missing_required_columns(frame: pd.DataFrame) -> list[str]:
    """Return missing contract columns for a TB_ED_VISITS-shaped dataframe."""

    return [column for column in TB_ED_VISITS_COLUMNS if column not in frame.columns]


def safe_constrained_projection(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop sensitive columns while preserving only known constrained fields."""

    keep = [column for column in CONSTRAINED_ANALYSIS_COLUMNS if column in frame.columns]
    return frame[keep].copy()
