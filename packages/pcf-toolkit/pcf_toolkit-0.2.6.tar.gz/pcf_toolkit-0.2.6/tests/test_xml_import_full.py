"""Tests for comprehensive XML import parsing."""

from __future__ import annotations

import pytest

from pcf_toolkit.xml_import import parse_manifest_xml_text


def test_import_full_manifest_sections() -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display" '
        'description-key="Sample_Desc" control-type="virtual" '
        'preview-image="preview.png">'
        '<property name="prop1" display-name-key="Prop1_Display" '
        'description-key="Prop1_Desc" of-type="SingleLine.Text" '
        'usage="bound" required="true" default-value="abc" '
        'pfx-default-value="pfx">'
        "<types><type>SingleLine.Text</type></types>"
        '<value name="val1" display-name-key="Val1_Display">1</value>'
        "</property>"
        '<event name="onChange" display-name-key="OnChange_Display" '
        'description-key="OnChange_Desc" pfx-default-value="evt" />'
        '<data-set name="ds1" display-name-key="DS_Display" '
        'description-key="DS_Desc" cds-data-set-options="true">'
        '<property-set name="set1" display-name-key="Set_Display" '
        'description-key="Set_Desc" of-type="Whole.None" usage="input" '
        'required="false">'
        "<types><type>Whole.None</type></types>"
        "</property-set>"
        "</data-set>"
        '<type-group name="group1"><type>Currency</type></type-group>'
        "<property-dependencies>"
        '<property-dependency input="prop1" output="prop2" required-for="schema" />'
        "</property-dependencies>"
        '<feature-usage><uses-feature name="Device" required="true" /></feature-usage>'
        '<external-service-usage enabled="true"><domain>example.com</domain></external-service-usage>'
        '<platform-action action-type="afterPageLoad" />'
        "<resources>"
        '<code path="index.ts" order="1" />'
        '<css path="style.css" order="1" />'
        '<img path="img.png" />'
        '<resx path="strings.resx" version="1.0.0" />'
        '<platform-library name="react" version="16.14.0" />'
        '<dependency type="control" name="lib.control" order="2" load-type="onDemand" />'
        "</resources>"
        "</control>"
        "</manifest>"
    )

    data = parse_manifest_xml_text(xml_text)
    control = data["control"]
    assert control["namespace"] == "Sample"
    assert control["description-key"] == "Sample_Desc"
    assert control["control-type"] == "virtual"
    assert control["preview-image"] == "preview.png"

    prop = control["property"][0]
    assert prop["required"] is True
    assert prop["types"]["type"][0]["value"] == "SingleLine.Text"
    assert prop["value"][0]["value"] == 1

    dataset = control["data-set"][0]
    prop_set = dataset["property-set"][0]
    assert prop_set["required"] is False
    assert prop_set["types"]["type"][0]["value"] == "Whole.None"

    assert control["type-group"][0]["name"] == "group1"
    assert control["property-dependencies"]["property-dependency"][0]["required-for"] == "schema"
    assert control["feature-usage"]["uses-feature"][0]["name"] == "Device"
    assert control["external-service-usage"]["enabled"] is True
    assert control["external-service-usage"]["domain"][0]["value"] == "example.com"
    assert control["platform-action"]["action-type"] == "afterPageLoad"

    resources = control["resources"]
    assert resources["code"]["order"] == 1
    assert resources["css"][0]["path"] == "style.css"
    assert resources["img"][0]["path"] == "img.png"
    assert resources["resx"][0]["version"] == "1.0.0"
    assert resources["platform-library"][0]["name"] == "react"
    assert resources["dependency"][0]["load-type"] == "onDemand"


def test_import_manifest_with_namespace() -> None:
    xml_text = (
        '<manifest xmlns="urn:pcf">'
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    data = parse_manifest_xml_text(xml_text)
    assert data["control"]["resources"]["code"]["path"] == "index.ts"


def test_import_int_and_value_edge_cases() -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display">'
        '<property name="prop1" display-name-key="Prop_Display" '
        'description-key="Prop_Desc" of-type="SingleLine.Text" usage="bound">'
        '<value name="val1" display-name-key="Val">not-an-int</value>'
        "</property>"
        "<resources>"
        '<code path="index.ts" order="" />'
        '<dependency type="control" name="lib.control" order="bad" />'
        "</resources>"
        "</control>"
        "</manifest>"
    )
    data = parse_manifest_xml_text(xml_text)
    prop = data["control"]["property"][0]
    assert prop["value"][0]["value"] == "not-an-int"
    resources = data["control"]["resources"]
    assert "order" not in resources["code"]
    assert resources["dependency"][0]["order"] == "bad"


def test_import_missing_control_element() -> None:
    with pytest.raises(ValueError):
        parse_manifest_xml_text("<manifest></manifest>")
