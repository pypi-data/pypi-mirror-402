"""Tests for schema snapshot loading."""

from __future__ import annotations

import io
import json

import pytest

from pcf_toolkit import schema_snapshot


def test_load_schema_snapshot_has_elements() -> None:
    snapshot_text = schema_snapshot.load_schema_snapshot()
    data = json.loads(snapshot_text)
    assert "elements" in data


def test_read_package_snapshot_with_fake_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_text = '{"elements": {"manifest": {}}}'

    class FakeFiles:
        def joinpath(self, name: str) -> FakeFiles:
            return self

        def open(self, mode: str = "r", encoding: str | None = None):
            return io.StringIO(fake_text)

    monkeypatch.setattr(schema_snapshot.resources, "files", lambda _: FakeFiles())
    assert schema_snapshot._read_package_snapshot() == fake_text


def test_read_package_snapshot_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_name: str):
        raise ModuleNotFoundError("missing")

    monkeypatch.setattr(schema_snapshot.resources, "files", _raise)
    assert schema_snapshot._read_package_snapshot() is None


def test_load_schema_snapshot_fallback(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "spec_raw.json").write_text('{"fallback": true}', encoding="utf-8")
    monkeypatch.setattr(schema_snapshot, "_read_package_snapshot", lambda: None)
    monkeypatch.chdir(tmp_path)
    snapshot = schema_snapshot.load_schema_snapshot()
    assert json.loads(snapshot)["fallback"] is True
