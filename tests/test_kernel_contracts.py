from __future__ import annotations

import pandas as pd
from pathlib import Path

from ed_flow.data_contracts import TB_ED_VISITS_COLUMNS
from ed_flow_kernel.contracts.semantic_views import semantic_view_contracts
from ed_flow_kernel.contracts.tb_ed_visits import TbEdVisitsContract, missing_required_columns, safe_constrained_projection
from ed_flow_kernel.forecasting.baselines import moving_average, seasonal_naive


def test_tb_ed_visits_kernel_contract_exposes_safe_projection() -> None:
    contract = TbEdVisitsContract()
    assert contract.table_name == "TB_ED_VISITS"
    assert "PATIENT_PHN" in contract.sensitive_columns
    frame = pd.DataFrame([{column: "x" for column in TB_ED_VISITS_COLUMNS}])
    projected = safe_constrained_projection(frame)
    assert "PATIENT_PHN" not in projected.columns
    assert missing_required_columns(frame) == []


def test_semantic_view_contracts_are_available_without_snowflake() -> None:
    contracts = semantic_view_contracts()
    assert {item.view_name for item in contracts} >= {"SV_EDPROVIDER_NOTES", "SV_LAB_REPORTS"}


def test_kernel_baselines_are_deterministic() -> None:
    series = pd.Series([1, 2, 3, 4])
    assert seasonal_naive(series, 5, season=2).tolist() == [3.0, 4.0, 3.0, 4.0, 3.0]
    assert moving_average(series, 3, window=2).tolist() == [3.5, 3.5, 3.5]


def test_kernel_modules_do_not_import_ui_frameworks() -> None:
    kernel_root = Path("packages/ed_flow_kernel/ed_flow_kernel")
    forbidden = ["import streamlit", "from streamlit", "from next", "import next", "from react", "import react"]
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in forbidden), path
