"""Compatibility entry point for the shared ED Flow capability kernel.

The implementation lives under ``packages/ed_flow_kernel/ed_flow_kernel`` so the
kernel can later become an installable package. This lightweight wrapper keeps
``python -m ed_flow_kernel...`` working from the repository root.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
KERNEL_SRC = ROOT / "packages" / "ed_flow_kernel" / "ed_flow_kernel"

for path in [SRC, KERNEL_SRC]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

if KERNEL_SRC.exists() and str(KERNEL_SRC) not in __path__:
    __path__.append(str(KERNEL_SRC))

__version__ = "0.4.0"
