"""Quality, freshness, and linkage checks for v2."""

from __future__ import annotations

import pandas as pd


def public_data_quality_summary(public_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarize local public/open-data cache health."""

    rows = []
    for name, frame in public_data.items():
        completeness = 1.0 - float(frame.isna().mean().mean()) if not frame.empty else 0.0
        rows.append(
            {
                "dataset": name,
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "completeness": completeness,
                "contains_patient_data": False,
                "status": "synthetic fallback available" if not frame.empty else "missing",
            }
        )
    return pd.DataFrame(rows)


def constrained_boundary_check(frame: pd.DataFrame, allowed_columns: list[str]) -> pd.DataFrame:
    """Report whether a dataframe stays inside the constrained data contract."""

    columns = sorted(frame.columns)
    disallowed = sorted(set(columns) - set(allowed_columns))
    return pd.DataFrame(
        [
            {
                "checked_columns": len(columns),
                "allowed_columns": len(set(columns) & set(allowed_columns)),
                "disallowed_columns": ", ".join(disallowed) if disallowed else "None",
                "passes": not disallowed,
            }
        ]
    )
