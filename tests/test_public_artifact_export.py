from __future__ import annotations

import json
from pathlib import Path

from ed_flow_kernel.exports.public_showcase_export import ARTIFACT_NAMES, export_public_showcase_artifacts
from ed_flow_kernel.governance.privacy import public_payload_has_phi_like_values


def test_public_artifact_export_creates_required_json(tmp_path: Path) -> None:
    written = export_public_showcase_artifacts(tmp_path, mode="public_demo", seed=20260601)
    assert {path.name for path in written} == set(ARTIFACT_NAMES)
    for path in written:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["data_mode"] == "public_demo"
        assert data["synthetic_flag"] is True
        assert "payload" in data
        assert not public_payload_has_phi_like_values(data)


def test_showcase_static_artifacts_are_present() -> None:
    public_data_dir = Path("apps/public_showcase/public/data")
    missing = [name for name in ARTIFACT_NAMES if not (public_data_dir / name).exists()]
    assert missing == []
