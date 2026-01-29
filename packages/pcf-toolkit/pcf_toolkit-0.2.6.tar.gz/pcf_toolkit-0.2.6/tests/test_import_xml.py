"""Validate XML import round-trip for manifest examples."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from pcf_toolkit.models import Manifest
from pcf_toolkit.xml import ManifestXmlSerializer
from pcf_toolkit.xml_import import parse_manifest_xml_text

SPEC_PATH = Path("data/spec_raw.json")


def _canonical(element: ET.Element) -> tuple:
    attrs = tuple(sorted(element.attrib.items()))
    text = (element.text or "").strip() or None
    children = tuple(_canonical(child) for child in list(element))
    return (element.tag, attrs, text, children)


def test_import_manifest_roundtrip() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    xml_text = next(p for p in spec["pages"] if p["slug"] == "manifest")["code_blocks"][0]["code"]

    raw = parse_manifest_xml_text(xml_text)
    manifest = Manifest.model_validate(raw)
    xml_out = ManifestXmlSerializer().to_string(manifest)

    assert _canonical(ET.fromstring(xml_out)) == _canonical(ET.fromstring(xml_text))


def test_import_yaml_dump_is_serializable() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    xml_text = next(p for p in spec["pages"] if p["slug"] == "manifest")["code_blocks"][0]["code"]

    raw = parse_manifest_xml_text(xml_text)
    manifest = Manifest.model_validate(raw)
    data = manifest.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude_defaults=True,
        mode="json",
    )

    yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
