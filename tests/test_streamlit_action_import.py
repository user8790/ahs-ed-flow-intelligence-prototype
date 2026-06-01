from __future__ import annotations

import importlib.util
from pathlib import Path


def test_streamlit_action_app_imports_without_snowflake_credentials() -> None:
    path = Path("apps/streamlit_action_intelligence/app.py")
    spec = importlib.util.spec_from_file_location("streamlit_action_app", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "main")
