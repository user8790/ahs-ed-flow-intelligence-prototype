"""Open-data feature builders."""

from __future__ import annotations

import pandas as pd

from ed_flow_intelligence.modeling import build_public_feature_matrix


def site_hour_public_features(public_data: dict[str, pd.DataFrame], facility: str) -> pd.DataFrame:
    """Return site-hour public pressure features."""

    return build_public_feature_matrix(public_data, facility)
