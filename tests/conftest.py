from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
KERNEL = ROOT / "packages" / "ed_flow_kernel"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(KERNEL) not in sys.path:
    sys.path.insert(0, str(KERNEL))
