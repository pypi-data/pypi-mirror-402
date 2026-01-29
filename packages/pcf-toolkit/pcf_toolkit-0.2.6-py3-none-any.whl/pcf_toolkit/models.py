"""Pydantic models for PCF manifest schema."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator, model_validator

from pcf_toolkit.types import (
    UNSUPPORTED_TYPE_VALUES,
    ControlType,
    DependencyLoadType,
    DependencyType,
    PlatformActionType,
    PlatformLibraryName,
    PropertySetUsage,
    PropertyUsage,
    RequiredFor,
    TypeValue,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class PcfBaseModel(BaseModel):
    """Base model with strict validation for PCF schema."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class EnumValue(PcfBaseModel):
    """Represents a value element for Enum types."""

    name: NonEmptyStr = Field(description="Name of the enum value.")
    display_name_key: NonEmptyStr = Field(
        alias="display-name-key",
        description="Localized display name for the enum value.",
    )
    value: int = Field(description="Numeric value for the enum option.")


class TypeElement(PcfBaseModel):
    """Represents a type element inside types or type-group."""

    value: TypeValue = Field(description="Data type value for the type element.")


class TypesElement(PcfBaseModel):
    """Represents a types element containing type children."""

    types: list[TypeElement] = Field(
        default_factory=list,
        alias="type",
        description="List of type elements.",
    )

    @model_validator(mode="after")
    def _ensure_not_empty(self) -> TypesElement:
        if not self.types:
            raise ValueError("types must include at least one type")
        return self


class TypeGroup(PcfBaseModel):
    """Defines a type-group element."""

    name: NonEmptyStr = Field(description="Name of the data type group.")
    types: list[TypeElement] = Field(
        default_factory=list,
        alias="type",
        description="Types belonging to the type-group.",
    )

    @model_validator(mode="after")
    def _ensure_types(self) -> TypeGroup:
        if not self.types:
            raise ValueError("type-group must include at least one type")
        return self


class Code(PcfBaseModel):
    """Represents a code element."""

    path: NonEmptyStr = Field(description="Place where the resource files are located.")
    order: PositiveInt = Field(description="The order in which the resource files should load.")


class Css(PcfBaseModel):
    """Represents a css element."""

    path: NonEmptyStr = Field(description="Relative path where CSS files are located.")
    order: PositiveInt | None = Field(
        default=None,
        description="The order in which the CSS files should load.",
    )


class Img(PcfBaseModel):
    """Represents an img element."""

    path: NonEmptyStr = Field(description="Relative path where image files are located.")


class Resx(PcfBaseModel):
    """Represents a resx element."""

    path: NonEmptyStr = Field(description="Relative path where resx files are located.")
    version: NonEmptyStr = Field(description="The current version of the resx file.")


class PlatformLibrary(PcfBaseModel):
    """Represents a platform-library element."""

    name: PlatformLibraryName = Field(description="Either React or Fluent.")
    version: NonEmptyStr = Field(description="The current version of the platform library.")


class Dependency(PcfBaseModel):
    """Represents a dependency element."""

    type: DependencyType = Field(description="Set to control.")
    name: NonEmptyStr = Field(description="Schema name of the library component.")
    order: PositiveInt | None = Field(default=None, description="The order in which the dependent library should load.")
    load_type: DependencyLoadType | None = Field(default=None, alias="load-type", description="Set to onDemand.")


class Resources(PcfBaseModel):
    """Represents a resources element."""

    code: Code = Field(description="Code resource definition.")
    css: list[Css] = Field(default_factory=list, description="CSS resources.")
    img: list[Img] = Field(default_factory=list, description="Image resources.")
    resx: list[Resx] = Field(default_factory=list, description="Resx resources.")
    platform_library: list[PlatformLibrary] = Field(
        default_factory=list, alias="platform-library", description="Platform library resources."
    )
    dependency: list[Dependency] = Field(default_factory=list, description="Dependent library resources.")


class Domain(PcfBaseModel):
    """Represents a domain element within external-service-usage."""

    value: NonEmptyStr = Field(description="Domain name used by the component.")


class ExternalServiceUsage(PcfBaseModel):
    """Represents external-service-usage element."""

    enabled: bool | None = Field(
        default=None,
        description=("Indicates whether this control uses an external service."),
    )
    domain: list[Domain] = Field(default_factory=list, description="Domains referenced by the control.")

    @model_validator(mode="after")
    def _enabled_requires_domains(self) -> ExternalServiceUsage:
        if self.enabled and not self.domain:
            raise ValueError("enabled external-service-usage requires at least one domain")
        return self


class PlatformAction(PcfBaseModel):
    """Represents a platform-action element."""

    action_type: PlatformActionType | None = Field(
        default=None,
        alias="action-type",
        description="Set to afterPageLoad.",
    )


class PropertyDependency(PcfBaseModel):
    """Represents a property-dependency element."""

    input: NonEmptyStr = Field(description="The name of the input property.")
    output: NonEmptyStr = Field(description="The name of the output property.")
    required_for: RequiredFor = Field(
        alias="required-for",
        description="Currently supported value is schema.",
    )


class PropertyDependencies(PcfBaseModel):
    """Represents property-dependencies element."""

    property_dependency: list[PropertyDependency] = Field(
        default_factory=list, alias="property-dependency", description="Property dependency definitions."
    )

    @model_validator(mode="after")
    def _ensure_dependencies(self) -> PropertyDependencies:
        if not self.property_dependency:
            raise ValueError("property-dependencies must include at least one property-dependency")
        return self


class UsesFeature(PcfBaseModel):
    """Represents a uses-feature element."""

    name: NonEmptyStr = Field(description="Name of the feature declared by the component.")
    required: bool = Field(description="Indicates if the component requires the feature.")


class FeatureUsage(PcfBaseModel):
    """Represents a feature-usage element."""

    uses_feature: list[UsesFeature] = Field(
        default_factory=list, alias="uses-feature", description="Features used by the component."
    )

    @model_validator(mode="after")
    def _ensure_uses_feature(self) -> FeatureUsage:
        if not self.uses_feature:
            raise ValueError("feature-usage must include at least one uses-feature")
        return self


class Event(PcfBaseModel):
    """Represents an event element."""

    name: NonEmptyStr = Field(description="Name of the event.")
    display_name_key: NonEmptyStr | None = Field(
        default=None, alias="display-name-key", description="Localized display name for the event."
    )
    description_key: NonEmptyStr | None = Field(
        default=None, alias="description-key", description="Localized description for the event."
    )
    pfx_default_value: NonEmptyStr | None = Field(
        default=None, alias="pfx-default-value", description="Default Power Fx expression for the event."
    )


class Property(PcfBaseModel):
    """Represents a property element."""

    name: NonEmptyStr = Field(description="Name of the property.")
    display_name_key: NonEmptyStr | None = Field(
        default=None, alias="display-name-key", description="Localized display name for the property."
    )
    description_key: NonEmptyStr | None = Field(
        default=None, alias="description-key", description="Localized description for the property."
    )
    of_type: TypeValue | None = Field(
        default=None, alias="of-type", description="Defines the data type of the property."
    )
    of_type_group: NonEmptyStr | None = Field(
        default=None, alias="of-type-group", description="Name of the type-group as defined in manifest."
    )
    usage: PropertyUsage | None = Field(default=None, description="Identifies the usage of the property.")
    required: bool | None = Field(default=None, description="Whether the property is required or not.")
    default_value: NonEmptyStr | None = Field(
        default=None, alias="default-value", description="Default configuration value provided to the component."
    )
    pfx_default_value: NonEmptyStr | None = Field(
        default=None,
        alias="pfx-default-value",
        description="Default Power Fx expression value provided to the component.",
    )
    types: TypesElement | None = Field(default=None, description="Types element for this property.")
    values: list[EnumValue] = Field(
        default_factory=list, alias="value", description="Enum values when of-type is Enum."
    )

    @field_validator("of_type")
    @classmethod
    def _validate_supported_type(cls, value: TypeValue | None) -> TypeValue | None:
        if value is None:
            return value
        if value.value in UNSUPPORTED_TYPE_VALUES:
            raise ValueError(f"Unsupported of-type value: {value.value}")
        return value

    @model_validator(mode="after")
    def _validate_type_requirements(self) -> Property:
        if not self.of_type and not self.of_type_group:
            raise ValueError("property requires of-type or of-type-group")
        if self.of_type == TypeValue.ENUM and not self.values:
            raise ValueError("Enum properties require at least one value element")
        return self


class PropertySet(PcfBaseModel):
    """Represents a property-set element within a data-set."""

    name: NonEmptyStr = Field(description="Name of the column.")
    display_name_key: NonEmptyStr = Field(
        alias="display-name-key", description="Localized display name for the property set."
    )
    description_key: NonEmptyStr | None = Field(
        default=None, alias="description-key", description="Localized description for the property set."
    )
    of_type: TypeValue | None = Field(
        default=None, alias="of-type", description="Defines the data type of the property set."
    )
    of_type_group: NonEmptyStr | None = Field(
        default=None, alias="of-type-group", description="Name of the type-group as defined in manifest."
    )
    usage: PropertySetUsage | None = Field(default=None, description="Usage value for the property set.")
    required: bool | None = Field(default=None, description="Indicates whether the property is required.")
    types: TypesElement | None = Field(default=None, description="Types element for this property set.")

    @field_validator("of_type")
    @classmethod
    def _validate_supported_type(cls, value: TypeValue | None) -> TypeValue | None:
        if value is None:
            return value
        if value.value in UNSUPPORTED_TYPE_VALUES:
            raise ValueError(f"Unsupported of-type value: {value.value}")
        return value

    @model_validator(mode="after")
    def _validate_type_requirements(self) -> PropertySet:
        if not self.of_type and not self.of_type_group:
            raise ValueError("property-set requires of-type or of-type-group")
        return self


class DataSet(PcfBaseModel):
    """Represents a data-set element."""

    name: NonEmptyStr = Field(description="Name of the grid.")
    display_name_key: NonEmptyStr = Field(alias="display-name-key", description="Defines the name of the property.")
    description_key: NonEmptyStr | None = Field(
        default=None, alias="description-key", description="Defines the description of the property."
    )
    cds_data_set_options: NonEmptyStr | None = Field(
        default=None,
        alias="cds-data-set-options",
        description=("Displays the Commandbar, ViewSelector, QuickFind if set to true."),
    )
    property_set: list[PropertySet] = Field(
        default_factory=list, alias="property-set", description="Property sets defined within the dataset."
    )


class Control(PcfBaseModel):
    """Represents a control element."""

    namespace: NonEmptyStr = Field(description="Defines the object prototype of the component.")
    constructor: NonEmptyStr = Field(description="A method for initializing the object.")
    version: NonEmptyStr = Field(description="Semantic version of the component.")
    display_name_key: NonEmptyStr = Field(
        alias="display-name-key", description="Defines the name of the control visible in the UI."
    )
    description_key: NonEmptyStr | None = Field(
        default=None, alias="description-key", description="Defines the description of the component visible in the UI."
    )
    control_type: ControlType | None = Field(
        default=None, alias="control-type", description="Defines whether the control is standard or virtual."
    )
    preview_image: NonEmptyStr | None = Field(
        default=None, alias="preview-image", description="Image used on customization screens."
    )

    property: list[Property] = Field(default_factory=list, description="Property definitions.")
    event: list[Event] = Field(default_factory=list, description="Event definitions.")
    data_set: list[DataSet] = Field(default_factory=list, alias="data-set", description="Data set definitions.")
    type_group: list[TypeGroup] = Field(default_factory=list, alias="type-group", description="Type group definitions.")
    property_dependencies: PropertyDependencies | None = Field(
        default=None, alias="property-dependencies", description="Property dependency definitions."
    )
    feature_usage: FeatureUsage | None = Field(
        default=None, alias="feature-usage", description="Feature usage definitions."
    )
    external_service_usage: ExternalServiceUsage | None = Field(
        default=None, alias="external-service-usage", description="External service usage definition."
    )
    platform_action: PlatformAction | None = Field(
        default=None, alias="platform-action", description="Platform action configuration."
    )
    resources: Resources = Field(description="Resource definitions.")

    @field_validator("namespace", "constructor")
    @classmethod
    def _validate_alpha_num(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("Value must contain only letters or numbers")
        return value


class Manifest(PcfBaseModel):
    """Represents the manifest root element."""

    control: Control = Field(description="Control definition.")
