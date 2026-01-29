"""Tests for CLI helper utilities."""

from __future__ import annotations

import pytest

from pcf_toolkit import cli_helpers


def test_render_validation_table() -> None:
    errors = [{"loc": ("control", "namespace"), "msg": "Required", "type": "missing"}]
    rendered = cli_helpers.render_validation_table(errors, title="Errors", stderr=False)
    assert rendered is True


def test_render_validation_table_without_rich(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_helpers, "Console", None)
    monkeypatch.setattr(cli_helpers, "Table", None)
    errors = [{"loc": ("control", "namespace"), "msg": "Required", "type": "missing"}]
    rendered = cli_helpers.render_validation_table(errors, title="Errors", stderr=False)
    assert rendered is False
    assert cli_helpers.rich_console() is None


def test_render_validation_table_without_console(monkeypatch: pytest.MonkeyPatch) -> None:
    errors = [{"loc": ("control",), "msg": "Required", "type": "missing"}]
    monkeypatch.setattr(cli_helpers, "Table", object())
    monkeypatch.setattr(cli_helpers, "rich_console", lambda stderr=False: None)
    rendered = cli_helpers.render_validation_table(errors, title="Errors", stderr=False)
    assert rendered is False
