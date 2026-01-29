"""Tests for internal CLI helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
from pydantic import ValidationError

from pcf_toolkit.cli import (
    _autocomplete_xml_path,
    _render_validation_error,
    _validate_xml_path,
)
from pcf_toolkit.models import Manifest


def test_validate_xml_path_requires_xml(tmp_path: Path) -> None:
    non_xml = tmp_path / "file.txt"
    non_xml.write_text("test", encoding="utf-8")
    with pytest.raises(typer.BadParameter):
        _validate_xml_path(str(non_xml))


def test_validate_xml_path_directory(tmp_path: Path) -> None:
    with pytest.raises(typer.BadParameter):
        _validate_xml_path(str(tmp_path))


def test_autocomplete_xml_path_filters_extensions(tmp_path: Path) -> None:
    xml_file = tmp_path / "file.xml"
    other_file = tmp_path / "file.txt"
    xml_file.write_text("<manifest />", encoding="utf-8")
    other_file.write_text("nope", encoding="utf-8")
    completions = _autocomplete_xml_path(None, [], str(tmp_path / "fi"))  # type: ignore[arg-type]
    assert any(str(xml_file) == item for item in completions)
    assert all(not item.endswith(".txt") for item in completions)


def test_render_validation_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_table(*_args, **_kwargs):
        return False

    monkeypatch.setattr("pcf_toolkit.cli.render_validation_table", _fake_table)
    with pytest.raises(ValidationError) as exc_info:
        Manifest.model_validate({"control": {"namespace": "Bad", "constructor": "Nope"}})
    _render_validation_error(exc_info.value)
