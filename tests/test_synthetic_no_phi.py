from __future__ import annotations

import json
from pathlib import Path

from ed_flow_kernel.governance.privacy import public_payload_has_phi_like_values


def test_public_showcase_artifacts_have_no_phi_like_values() -> None:
    for path in Path("apps/public_showcase/public/data").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert not public_payload_has_phi_like_values(data), path.name
