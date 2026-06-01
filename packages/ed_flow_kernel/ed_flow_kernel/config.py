"""Kernel runtime configuration without UI dependencies."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class KernelConfig(BaseModel):
    """Paths and mode flags shared by Streamlit, exports, and tests."""

    repo_root: Path = Field(default_factory=lambda: _find_repo_root(Path.cwd()))
    data_mode: str = "public_demo"
    default_facility: str = "Stollery Children's Hospital"
    synthetic_flag: bool = True

    @property
    def synthetic_data_dir(self) -> Path:
        return self.repo_root / "data" / "synthetic"

    @property
    def open_data_dir(self) -> Path:
        return self.repo_root / "data" / "open"


def _find_repo_root(start: Path) -> Path:
    """Walk upward until the repository root is found."""

    for path in [start, *start.parents]:
        if (path / "requirements.txt").exists() and (path / "src").exists():
            return path
    return start
