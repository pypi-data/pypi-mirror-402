"""Tests for manifest I/O helpers."""

from __future__ import annotations

import json
from pathlib import Path

from pcf_toolkit.io import load_manifest


def _minimal_manifest_dict() -> dict[str, object]:
    return {
        "control": {
            "namespace": "Sample",
            "constructor": "SampleControl",
            "version": "1.0.0",
            "display-name-key": "Sample_Display",
            "control-type": "virtual",
            "resources": {"code": {"path": "index.ts", "order": 1}},
        }
    }


def test_load_manifest_from_json_file(tmp_path: Path) -> None:
    data = _minimal_manifest_dict()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    manifest = load_manifest(str(path))
    assert manifest.control.namespace == "Sample"


def test_load_manifest_from_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        "\n".join(
            [
                "control:",
                "  namespace: Sample",
                "  constructor: SampleControl",
                "  version: 1.0.0",
                "  display-name-key: Sample_Display",
                "  control-type: virtual",
                "  resources:",
                "    code:",
                "      path: index.ts",
                "      order: 1",
            ]
        ),
        encoding="utf-8",
    )
    manifest = load_manifest(str(path))
    assert manifest.control.constructor == "SampleControl"


def test_load_manifest_auto_detect_json(tmp_path: Path) -> None:
    data = _minimal_manifest_dict()
    path = tmp_path / "manifest.txt"
    path.write_text(json.dumps(data), encoding="utf-8")
    manifest = load_manifest(str(path))
    assert manifest.control.version == "1.0.0"
