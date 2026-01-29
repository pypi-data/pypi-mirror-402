"""Validate XML serialization against documentation examples."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from pcf_toolkit.models import (
    Code,
    Control,
    Css,
    DataSet,
    Dependency,
    Domain,
    EnumValue,
    Event,
    ExternalServiceUsage,
    FeatureUsage,
    Img,
    Manifest,
    PlatformAction,
    PlatformLibrary,
    Property,
    PropertyDependencies,
    PropertyDependency,
    Resources,
    Resx,
    TypeElement,
    TypeGroup,
    UsesFeature,
)
from pcf_toolkit.types import (
    ControlType,
    DependencyLoadType,
    DependencyType,
    PlatformActionType,
    PlatformLibraryName,
    PropertyUsage,
    RequiredFor,
    TypeValue,
)
from pcf_toolkit.xml import ManifestXmlSerializer

SPEC_PATH = Path("data/spec_raw.json")


def _load_example(slug: str, heading: str | None = None) -> str:
    data = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    page = next(p for p in data["pages"] if p["slug"] == slug)
    if heading is None:
        return page["code_blocks"][0]["code"]
    for block in page["code_blocks"]:
        if block.get("heading") == heading:
            return block["code"]
    raise KeyError(f"Example not found for {slug} heading {heading}")


def _canonical(element: ET.Element) -> tuple:
    attrs = tuple(sorted(element.attrib.items()))
    text = (element.text or "").strip() or None
    children = tuple(_canonical(child) for child in list(element))
    return (element.tag, attrs, text, children)


def _parse_fragment(xml_fragment: str) -> ET.Element:
    wrapped = f"<root>{xml_fragment}</root>"
    root = ET.fromstring(wrapped)
    return list(root)[0]


def _parse_children(xml_fragment: str) -> list[ET.Element]:
    wrapped = f"<root>{xml_fragment}</root>"
    root = ET.fromstring(wrapped)
    return list(root)


def _canonical_list(elements: list[ET.Element]) -> list[tuple]:
    return [_canonical(element) for element in elements]


def test_manifest_example() -> None:
    manifest = Manifest(
        control=Control(
            namespace="MyNameSpace",
            constructor="JSHelloWorldControl",
            version="1.0.0",
            display_name_key="JS_HelloWorldControl_Display_Key",
            description_key="JS_HelloWorldControl_Desc_Key",
            control_type=ControlType.STANDARD,
            property=[
                Property(
                    name="myFirstProperty",
                    display_name_key="myFirstProperty_Display_Key",
                    description_key="myFirstProperty_Desc_Key",
                    of_type=TypeValue.SINGLE_LINE_TEXT,
                    usage=PropertyUsage.BOUND,
                    required=True,
                )
            ],
            resources=Resources(
                code=Code(path="JS_HelloWorldControl.js", order=1),
                css=[Css(path="css/JS_HelloWorldControl.css", order=1)],
            ),
        )
    )
    serializer = ManifestXmlSerializer(xml_declaration=True)
    expected = _load_example("manifest")
    actual = serializer.to_string(manifest)
    assert _canonical(ET.fromstring(actual)) == _canonical(ET.fromstring(expected))


def test_code_example_elements() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    expected = _parse_children(_load_example("code"))
    actual = [
        serializer._code_to_element(Code(path="TS_IncrementControl.js", order=1)),
        serializer._css_to_element(Css(path="css/TS_IncrementControl.css", order=1)),
        serializer._resx_to_element(Resx(path="strings/TSIncrementControl.1033.resx", version="1.0.0")),
    ]
    assert _canonical_list(actual) == _canonical_list(expected)


def test_css_example_resources() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    resources = Resources(
        code=Code(path="TS_LocalizationAPI.js", order=1),
        css=[Css(path="css/TS_LocalizationAPI.css", order=1)],
    )
    element = serializer._resources_to_element(resources)
    expected = _load_example("css")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_img_example_resources() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    resources = Resources(
        code=Code(path="index.ts", order=1),
        img=[Img(path="img/default.png")],
    )
    element = serializer._resources_to_element(resources)
    expected = _load_example("img")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_platform_library_example_resources() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    resources = Resources(
        code=Code(path="index.ts", order=1),
        platform_library=[
            PlatformLibrary(name=PlatformLibraryName.REACT, version="16.14.0"),
            PlatformLibrary(name=PlatformLibraryName.FLUENT, version="9.46.2"),
        ],
    )
    element = serializer._resources_to_element(resources)
    expected = _load_example("platform-library")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_resx_example_resources() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    resources = Resources(
        code=Code(path="TS_LocalizationAPI.js", order=1),
        css=[Css(path="css/TS_LocalizationAPI.css", order=1)],
        resx=[
            Resx(path="strings/TSLocalizationAPI.1033.resx", version="1.0.0"),
            Resx(path="strings/TSLocalizationAPI.1035.resx", version="1.0.0"),
            Resx(path="strings/TSLocalizationAPI.3082.resx", version="1.0.0"),
        ],
    )
    element = serializer._resources_to_element(resources)
    expected = _load_example("resx")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_dependency_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    dependency = Dependency(
        type=DependencyType.CONTROL,
        name="samples_SampleNS.SampleStubLibraryPCF",
        load_type=DependencyLoadType.ON_DEMAND,
    )
    element = serializer._dependency_to_element(dependency)
    expected = _load_example("dependency")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_platform_action_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    action = PlatformAction(action_type=PlatformActionType.AFTER_PAGE_LOAD)
    element = serializer._platform_action_to_element(action)
    expected = _load_example("platform-action")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_property_dependency_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    deps = PropertyDependencies(
        property_dependency=[
            PropertyDependency(
                input="Text",
                output="Photos",
                required_for=RequiredFor.SCHEMA,
            )
        ]
    )
    element = serializer._property_dependencies_to_element(deps)
    expected = _load_example("property-dependency")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_feature_usage_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    usage = FeatureUsage(
        uses_feature=[
            UsesFeature(name="Device.captureAudio", required=True),
            UsesFeature(name="Device.captureImage", required=True),
            UsesFeature(name="Device.captureVideo", required=True),
            UsesFeature(name="Device.getBarcodeValue", required=True),
            UsesFeature(name="Device.getCurrentPosition", required=True),
            UsesFeature(name="Device.pickFile", required=True),
            UsesFeature(name="Utility", required=True),
            UsesFeature(name="WebAPI", required=True),
        ]
    )
    element = serializer._feature_usage_to_element(usage)
    expected = _load_example("feature-usage")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_uses_feature_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    usage = FeatureUsage(uses_feature=[UsesFeature(name="WebAPI", required=True)])
    element = serializer._feature_usage_to_element(usage)
    expected = _load_example("uses-feature")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_property_enum_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    prop = Property(
        name="YesNo",
        display_name_key="YesNo_Display_Key",
        description_key="YesNo_Desc_Key",
        of_type=TypeValue.ENUM,
        usage=PropertyUsage.INPUT,
        required=False,
        values=[
            EnumValue(name="Yes", display_name_key="Yes", value=0),
            EnumValue(name="No", display_name_key="No", value=1),
        ],
    )
    element = serializer._property_to_element(prop)
    expected = _load_example("type", "Example for Enum type")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_external_service_usage_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    usage = ExternalServiceUsage(enabled=True, domain=[Domain(value="www.Microsoft.com")])
    element = serializer._external_service_usage_to_element(usage)
    expected = _load_example("external-service-usage", "Example 1")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_event_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    event = Event(
        name="OnSelectCustomButton",
        pfx_default_value="SubmitForm(%MyFormName.ID%); Back(%ScreenTransition.RESERVED%.Cover)",
        display_name_key="OnSelectCustomButton_Display_Key",
        description_key="OnSelectCustomButton_Desc_Key",
    )
    element = serializer._event_to_element(event)
    expected = _load_example("event")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_data_set_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    dataset = DataSet(
        name="dataSetGrid",
        display_name_key="DataSetGridProperty",
        cds_data_set_options="displayCommandBar:true;displayViewSelector:true;displayQuickFind:true",
    )
    element = serializer._dataset_to_element(dataset)
    expected = _load_example("data-set")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_resources_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    resources = Resources(
        code=Code(path="JS_HelloWorldControl.js", order=1),
        css=[Css(path="css/JS_HelloWorldControl.css", order=1)],
    )
    element = serializer._resources_to_element(resources)
    expected = _load_example("resources")
    assert _canonical(element) == _canonical(_parse_fragment(expected))


def test_type_group_example() -> None:
    serializer = ManifestXmlSerializer(xml_declaration=False)
    group = TypeGroup(
        name="numbers",
        types=[
            TypeElement(value=TypeValue.WHOLE_NONE),
            TypeElement(value=TypeValue.CURRENCY),
            TypeElement(value=TypeValue.FP),
            TypeElement(value=TypeValue.DECIMAL),
        ],
    )
    element = serializer._type_group_to_element(group)
    expected = _load_example("type-group", "Example")
    assert _canonical(element) == _canonical(_parse_fragment(expected))
