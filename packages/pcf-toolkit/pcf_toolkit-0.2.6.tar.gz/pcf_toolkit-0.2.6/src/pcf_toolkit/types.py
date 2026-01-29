"""Shared types and enums for PCF manifest models."""

from __future__ import annotations

from enum import Enum


class ControlType(str, Enum):
    """Defines the control type of a PCF component."""

    STANDARD = "standard"
    VIRTUAL = "virtual"


class DependencyType(str, Enum):
    """Defines the dependency type for a component."""

    CONTROL = "control"


class DependencyLoadType(str, Enum):
    """Defines how a dependency is loaded."""

    ON_DEMAND = "onDemand"


class PlatformActionType(str, Enum):
    """Defines platform action types."""

    AFTER_PAGE_LOAD = "afterPageLoad"


class PlatformLibraryName(str, Enum):
    """Platform library names for React controls and platform libraries."""

    REACT = "React"
    FLUENT = "Fluent"


class PropertyUsage(str, Enum):
    """Usage values for property elements."""

    BOUND = "bound"
    INPUT = "input"
    OUTPUT = "output"


class PropertySetUsage(str, Enum):
    """Usage values for property-set elements."""

    BOUND = "bound"
    INPUT = "input"


class RequiredFor(str, Enum):
    """Supported required-for values for property-dependency."""

    SCHEMA = "schema"


class TypeValue(str, Enum):
    """Supported data types for property and type elements."""

    CURRENCY = "Currency"
    DATE_AND_TIME = "DateAndTime.DateAndTime"
    DATE_ONLY = "DateAndTime.DateOnly"
    DECIMAL = "Decimal"
    ENUM = "Enum"
    FP = "FP"
    LOOKUP_SIMPLE = "Lookup.Simple"
    MULTIPLE = "Multiple"
    MULTI_SELECT_OPTION_SET = "MultiSelectOptionSet"
    OBJECT = "Object"
    OPTION_SET = "OptionSet"
    SINGLE_LINE_EMAIL = "SingleLine.Email"
    SINGLE_LINE_PHONE = "SingleLine.Phone"
    SINGLE_LINE_TEXT = "SingleLine.Text"
    SINGLE_LINE_TEXT_AREA = "SingleLine.TextArea"
    SINGLE_LINE_TICKER = "SingleLine.Ticker"
    SINGLE_LINE_URL = "SingleLine.URL"
    TWO_OPTIONS = "TwoOptions"
    WHOLE_NONE = "Whole.None"


UNSUPPORTED_TYPE_VALUES = {
    "Lookup.Customer",
    "Lookup.Owner",
    "Lookup.PartyList",
    "Lookup.Regarding",
    "Status Reason",
    "Status",
    "Whole.Duration",
    "Whole.Language",
    "Whole.TimeZone",
}
