"""Validation tests for model invariants."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pcf_toolkit.models import Code, Control, ExternalServiceUsage, Manifest, Resources
from pcf_toolkit.types import ControlType


def _minimal_control(namespace: str, constructor: str) -> Control:
    return Control(
        namespace=namespace,
        constructor=constructor,
        version="1.0.0",
        display_name_key="Display",
        control_type=ControlType.VIRTUAL,
        resources=Resources(code=Code(path="index.ts", order=1)),
    )


def test_control_namespace_requires_alnum() -> None:
    with pytest.raises(ValidationError):
        _minimal_control("Bad-Name", "Constructor")


def test_control_constructor_requires_alnum() -> None:
    with pytest.raises(ValidationError):
        _minimal_control("GoodName", "Bad-Name")


def test_external_service_usage_requires_domains_when_enabled() -> None:
    with pytest.raises(ValidationError):
        ExternalServiceUsage(enabled=True, domain=[])


def test_manifest_validates_control() -> None:
    control = _minimal_control("GoodName", "GoodConstructor")
    manifest = Manifest(control=control)
    assert manifest.control.namespace == "GoodName"
