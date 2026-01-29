"""Tests for full XML serialization paths."""

from __future__ import annotations

import xml.etree.ElementTree as ET

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
    Manifest,
    PlatformAction,
    PlatformLibrary,
    Property,
    PropertyDependencies,
    PropertyDependency,
    PropertySet,
    Resources,
    Resx,
    TypeElement,
    TypeGroup,
    TypesElement,
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


def test_full_manifest_serialization() -> None:
    manifest = Manifest(
        control=Control(
            namespace="Sample",
            constructor="SampleControl",
            version="1.0.0",
            display_name_key="Sample_Display",
            description_key="Sample_Desc",
            control_type=ControlType.VIRTUAL,
            preview_image="preview.png",
            property=[
                Property(
                    name="prop1",
                    display_name_key="Prop_Display",
                    description_key="Prop_Desc",
                    of_type=TypeValue.SINGLE_LINE_TEXT,
                    usage=PropertyUsage.BOUND,
                    required=True,
                    default_value="abc",
                    pfx_default_value="pfx",
                    types=TypesElement(types=[TypeElement(value=TypeValue.SINGLE_LINE_TEXT)]),
                    values=[
                        EnumValue(
                            name="one",
                            display_name_key="One",
                            value=1,
                        )
                    ],
                )
            ],
            event=[
                Event(
                    name="onChange",
                    display_name_key="OnChange_Display",
                    description_key="OnChange_Desc",
                    pfx_default_value="evt",
                )
            ],
            data_set=[
                DataSet(
                    name="ds1",
                    display_name_key="DS_Display",
                    description_key="DS_Desc",
                    cds_data_set_options="true",
                    property_set=[
                        PropertySet(
                            name="set1",
                            display_name_key="Set_Display",
                            description_key="Set_Desc",
                            of_type=TypeValue.WHOLE_NONE,
                            usage=PropertyUsage.INPUT,
                            required=False,
                            types=TypesElement(types=[TypeElement(value=TypeValue.WHOLE_NONE)]),
                        )
                    ],
                )
            ],
            type_group=[
                TypeGroup(
                    name="group1",
                    types=[TypeElement(value=TypeValue.CURRENCY)],
                )
            ],
            property_dependencies=PropertyDependencies(
                property_dependency=[
                    PropertyDependency(
                        input="prop1",
                        output="prop2",
                        required_for=RequiredFor.SCHEMA,
                    )
                ]
            ),
            feature_usage=FeatureUsage(uses_feature=[UsesFeature(name="Device", required=True)]),
            external_service_usage=ExternalServiceUsage(enabled=True, domain=[Domain(value="example.com")]),
            platform_action=PlatformAction(action_type=PlatformActionType.AFTER_PAGE_LOAD),
            resources=Resources(
                code=Code(path="index.ts", order=1),
                css=[Css(path="style.css", order=1)],
                resx=[Resx(path="strings.resx", version="1.0.0")],
                platform_library=[PlatformLibrary(name=PlatformLibraryName.REACT, version="16.14.0")],
                dependency=[
                    Dependency(
                        type=DependencyType.CONTROL,
                        name="lib.control",
                        order=2,
                        load_type=DependencyLoadType.ON_DEMAND,
                    )
                ],
            ),
        )
    )

    xml_text = ManifestXmlSerializer(xml_declaration=False).to_string(manifest)
    root = ET.fromstring(xml_text)
    assert root.find("control/resources/code") is not None
    assert root.find("control/feature-usage/uses-feature") is not None
    assert root.find("control/external-service-usage/domain") is not None
