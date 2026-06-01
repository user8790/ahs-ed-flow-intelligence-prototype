"""Local backend factory for synthetic/public-safe execution."""

from __future__ import annotations

from pathlib import Path

from ed_flow.local_backend import LocalBackend
from ed_flow.synthetic_data import ensure_synthetic_data


def create_local_backend(data_dir: str | Path) -> LocalBackend:
    """Create a local backend after ensuring synthetic rows exist."""

    path = Path(data_dir)
    ensure_synthetic_data(path)
    return LocalBackend(path)
