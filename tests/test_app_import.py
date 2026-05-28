from __future__ import annotations

import importlib


def test_app_imports_without_errors() -> None:
    app = importlib.import_module("app")

    assert hasattr(app, "main")

