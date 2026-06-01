"""Semantic chart-review view contracts for future Snowflake mode."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ed_flow.data_contracts import SEMANTIC_VIEW_COLUMNS


class SemanticViewContract(BaseModel):
    """Column-level metadata for a chart-review semantic view."""

    view_name: str
    columns: list[str]
    sensitive_identifier: str = "PAT_MRN_ID"
    public_mode: str = "unavailable; synthetic mock summaries only"


def semantic_view_contracts() -> list[SemanticViewContract]:
    """Return all configured semantic-view contracts."""

    return [
        SemanticViewContract(view_name=name, columns=columns)
        for name, columns in SEMANTIC_VIEW_COLUMNS.items()
    ]


class ChartReviewBoundary(BaseModel):
    """Boundary statement for chart-review data."""

    local_mode: str = "synthetic mock notes only"
    snowflake_mode: str = "governed semantic views with validated chart-number mapping"
    public_artifact_mode: str = "excluded"
    caveats: list[str] = Field(
        default_factory=lambda: [
            "Summaries are aids for human review, not clinical judgement.",
            "Identifier mapping must be validated before internal use.",
            "No chart-review text is exported to public artifacts.",
        ]
    )
