"""Import ControlManifest.Input.xml into manifest data."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from typing import Any


def parse_manifest_xml_path(path: str) -> dict[str, Any]:
    """Parses a manifest XML file into a dict suitable for Manifest validation.

    Args:
      path: Path to the XML file, or '-' to read from stdin.

    Returns:
      Dictionary representation of the manifest data.

    Raises:
      ValueError: If the XML structure is invalid.
    """
    if path == "-":
        xml_text = sys.stdin.read()
        return parse_manifest_xml_text(xml_text)
    tree = ET.parse(path)
    return parse_manifest_xml_element(tree.getroot())


def parse_manifest_xml_text(xml_text: str) -> dict[str, Any]:
    """Parses a manifest XML string into a dict suitable for Manifest validation.

    Args:
      xml_text: XML string content to parse.

    Returns:
      Dictionary representation of the manifest data.

    Raises:
      ValueError: If the XML structure is invalid.
    """
    root = ET.fromstring(xml_text)
    return parse_manifest_xml_element(root)


def parse_manifest_xml_element(root: ET.Element) -> dict[str, Any]:
    """Parses the manifest XML root element into a dict.

    Args:
      root: Root XML element (should be <manifest>).

    Returns:
      Dictionary representation of the manifest data.

    Raises:
      ValueError: If the root element is not <manifest> or missing <control>.
    """
    if _strip_ns(root.tag) != "manifest":
        raise ValueError("Root element must be <manifest>.")

    control_el = _first_child(root, "control")
    if control_el is None:
        raise ValueError("Manifest must contain a <control> element.")

    control = _parse_control(control_el)
    return {"control": control}


def _parse_control(control_el: ET.Element) -> dict[str, Any]:
    """Parses a control XML element into a dictionary.

    Args:
      control_el: XML element representing a control.

    Returns:
      Dictionary containing control data.
    """
    data: dict[str, Any] = {}
    _set_attr(data, control_el, "namespace")
    _set_attr(data, control_el, "constructor")
    _set_attr(data, control_el, "version")
    _set_attr(data, control_el, "display-name-key")
    _set_attr(data, control_el, "description-key")
    _set_attr(data, control_el, "control-type")
    _set_attr(data, control_el, "preview-image")

    data["property"] = [_parse_property(el) for el in _children(control_el, "property")]
    data["event"] = [_parse_event(el) for el in _children(control_el, "event")]
    data["data-set"] = [_parse_dataset(el) for el in _children(control_el, "data-set")]
    data["type-group"] = [_parse_type_group(el) for el in _children(control_el, "type-group")]

    prop_deps = _first_child(control_el, "property-dependencies")
    if prop_deps is not None:
        data["property-dependencies"] = _parse_property_dependencies(prop_deps)

    feature_usage = _first_child(control_el, "feature-usage")
    if feature_usage is not None:
        data["feature-usage"] = _parse_feature_usage(feature_usage)

    external_usage = _first_child(control_el, "external-service-usage")
    if external_usage is not None:
        data["external-service-usage"] = _parse_external_service_usage(external_usage)

    platform_action = _first_child(control_el, "platform-action")
    if platform_action is not None:
        data["platform-action"] = _parse_platform_action(platform_action)

    resources = _first_child(control_el, "resources")
    if resources is not None:
        data["resources"] = _parse_resources(resources)

    return data


def _parse_property(property_el: ET.Element) -> dict[str, Any]:
    """Parses a property XML element into a dictionary.

    Args:
      property_el: XML element representing a property.

    Returns:
      Dictionary containing property data.
    """
    data: dict[str, Any] = {}
    for attr in (
        "name",
        "display-name-key",
        "description-key",
        "of-type",
        "of-type-group",
        "usage",
        "default-value",
        "pfx-default-value",
    ):
        _set_attr(data, property_el, attr)
    _set_bool_attr(data, property_el, "required")

    types_el = _first_child(property_el, "types")
    if types_el is not None:
        data["types"] = _parse_types(types_el)

    values = [_parse_value(el) for el in _children(property_el, "value")]
    if values:
        data["value"] = values

    return data


def _parse_value(value_el: ET.Element) -> dict[str, Any]:
    """Parses a value XML element (enum value) into a dictionary.

    Args:
      value_el: XML element representing an enum value.

    Returns:
      Dictionary containing value data with name, display-name-key, and value.
    """
    data: dict[str, Any] = {}
    _set_attr(data, value_el, "name")
    _set_attr(data, value_el, "display-name-key")
    text = (value_el.text or "").strip()
    if text:
        try:
            data["value"] = int(text)
        except ValueError:
            data["value"] = text
    return data


def _parse_event(event_el: ET.Element) -> dict[str, Any]:
    """Parses an event XML element into a dictionary.

    Args:
      event_el: XML element representing an event.

    Returns:
      Dictionary containing event data.
    """
    data: dict[str, Any] = {}
    for attr in (
        "name",
        "display-name-key",
        "description-key",
        "pfx-default-value",
    ):
        _set_attr(data, event_el, attr)
    return data


def _parse_dataset(dataset_el: ET.Element) -> dict[str, Any]:
    """Parses a data-set XML element into a dictionary.

    Args:
      dataset_el: XML element representing a data set.

    Returns:
      Dictionary containing data set data.
    """
    data: dict[str, Any] = {}
    for attr in (
        "name",
        "display-name-key",
        "description-key",
        "cds-data-set-options",
    ):
        _set_attr(data, dataset_el, attr)
    data["property-set"] = [_parse_property_set(el) for el in _children(dataset_el, "property-set")]
    return data


def _parse_property_set(prop_set_el: ET.Element) -> dict[str, Any]:
    """Parses a property-set XML element into a dictionary.

    Args:
      prop_set_el: XML element representing a property set.

    Returns:
      Dictionary containing property set data.
    """
    data: dict[str, Any] = {}
    for attr in (
        "name",
        "display-name-key",
        "description-key",
        "of-type",
        "of-type-group",
        "usage",
    ):
        _set_attr(data, prop_set_el, attr)
    _set_bool_attr(data, prop_set_el, "required")
    types_el = _first_child(prop_set_el, "types")
    if types_el is not None:
        data["types"] = _parse_types(types_el)
    return data


def _parse_types(types_el: ET.Element) -> dict[str, Any]:
    """Parses a types XML element into a dictionary.

    Args:
      types_el: XML element containing type children.

    Returns:
      Dictionary with 'type' key containing list of type dictionaries.
    """
    types = []
    for type_el in _children(types_el, "type"):
        value = (type_el.text or "").strip()
        if value:
            types.append({"value": value})
    return {"type": types}


def _parse_type_group(type_group_el: ET.Element) -> dict[str, Any]:
    """Parses a type-group XML element into a dictionary.

    Args:
      type_group_el: XML element representing a type group.

    Returns:
      Dictionary containing type group data.
    """
    data: dict[str, Any] = {}
    _set_attr(data, type_group_el, "name")
    types = []
    for type_el in _children(type_group_el, "type"):
        value = (type_el.text or "").strip()
        if value:
            types.append({"value": value})
    data["type"] = types
    return data


def _parse_property_dependencies(deps_el: ET.Element) -> dict[str, Any]:
    """Parses property-dependencies XML element into a dictionary.

    Args:
      deps_el: XML element containing property-dependency children.

    Returns:
      Dictionary with 'property-dependency' key containing list of dependencies.
    """
    deps = []
    for dep_el in _children(deps_el, "property-dependency"):
        item: dict[str, Any] = {}
        for attr in ("input", "output", "required-for"):
            _set_attr(item, dep_el, attr)
        deps.append(item)
    return {"property-dependency": deps}


def _parse_feature_usage(feature_el: ET.Element) -> dict[str, Any]:
    """Parses feature-usage XML element into a dictionary.

    Args:
      feature_el: XML element containing uses-feature children.

    Returns:
      Dictionary with 'uses-feature' key containing list of features.
    """
    uses_features = []
    for use_el in _children(feature_el, "uses-feature"):
        item: dict[str, Any] = {}
        _set_attr(item, use_el, "name")
        _set_bool_attr(item, use_el, "required")
        uses_features.append(item)
    return {"uses-feature": uses_features}


def _parse_external_service_usage(usage_el: ET.Element) -> dict[str, Any]:
    """Parses external-service-usage XML element into a dictionary.

    Args:
      usage_el: XML element representing external service usage.

    Returns:
      Dictionary containing external service usage data.
    """
    data: dict[str, Any] = {}
    _set_bool_attr(data, usage_el, "enabled")
    domains = []
    for dom_el in _children(usage_el, "domain"):
        text = (dom_el.text or "").strip()
        if text:
            domains.append({"value": text})
    if domains:
        data["domain"] = domains
    return data


def _parse_platform_action(action_el: ET.Element) -> dict[str, Any]:
    """Parses platform-action XML element into a dictionary.

    Args:
      action_el: XML element representing a platform action.

    Returns:
      Dictionary containing platform action data.
    """
    data: dict[str, Any] = {}
    _set_attr(data, action_el, "action-type")
    return data


def _parse_resources(resources_el: ET.Element) -> dict[str, Any]:
    """Parses resources XML element into a dictionary.

    Args:
      resources_el: XML element containing resource children.

    Returns:
      Dictionary containing all resource data (code, css, img, resx, etc.).
    """
    data: dict[str, Any] = {}
    code_el = _first_child(resources_el, "code")
    if code_el is not None:
        data["code"] = _parse_code(code_el)

    data["css"] = [_parse_css(el) for el in _children(resources_el, "css")]
    data["img"] = [_parse_img(el) for el in _children(resources_el, "img")]
    data["resx"] = [_parse_resx(el) for el in _children(resources_el, "resx")]
    data["platform-library"] = [_parse_platform_library(el) for el in _children(resources_el, "platform-library")]
    data["dependency"] = [_parse_dependency(el) for el in _children(resources_el, "dependency")]
    return data


def _parse_code(code_el: ET.Element) -> dict[str, Any]:
    """Parses a code XML element into a dictionary.

    Args:
      code_el: XML element representing a code resource.

    Returns:
      Dictionary containing code resource data (path, order).
    """
    data: dict[str, Any] = {}
    _set_attr(data, code_el, "path")
    _set_int_attr(data, code_el, "order")
    return data


def _parse_css(css_el: ET.Element) -> dict[str, Any]:
    """Parses a css XML element into a dictionary.

    Args:
      css_el: XML element representing a CSS resource.

    Returns:
      Dictionary containing CSS resource data (path, order).
    """
    data: dict[str, Any] = {}
    _set_attr(data, css_el, "path")
    _set_int_attr(data, css_el, "order")
    return data


def _parse_img(img_el: ET.Element) -> dict[str, Any]:
    """Parses an img XML element into a dictionary.

    Args:
      img_el: XML element representing an image resource.

    Returns:
      Dictionary containing image resource data (path).
    """
    data: dict[str, Any] = {}
    _set_attr(data, img_el, "path")
    return data


def _parse_resx(resx_el: ET.Element) -> dict[str, Any]:
    """Parses a resx XML element into a dictionary.

    Args:
      resx_el: XML element representing a resx resource.

    Returns:
      Dictionary containing resx resource data (path, version).
    """
    data: dict[str, Any] = {}
    _set_attr(data, resx_el, "path")
    _set_attr(data, resx_el, "version")
    return data


def _parse_platform_library(lib_el: ET.Element) -> dict[str, Any]:
    """Parses a platform-library XML element into a dictionary.

    Args:
      lib_el: XML element representing a platform library.

    Returns:
      Dictionary containing platform library data (name, version).
    """
    data: dict[str, Any] = {}
    _set_attr(data, lib_el, "name")
    _set_attr(data, lib_el, "version")
    return data


def _parse_dependency(dep_el: ET.Element) -> dict[str, Any]:
    """Parses a dependency XML element into a dictionary.

    Args:
      dep_el: XML element representing a dependency.

    Returns:
      Dictionary containing dependency data (type, name, order, load-type).
    """
    data: dict[str, Any] = {}
    _set_attr(data, dep_el, "type")
    _set_attr(data, dep_el, "name")
    _set_int_attr(data, dep_el, "order")
    _set_attr(data, dep_el, "load-type")
    return data


def _strip_ns(tag: str) -> str:
    """Strips XML namespace prefix from a tag name.

    Args:
      tag: Tag name potentially with namespace prefix (e.g., "{ns}tag").

    Returns:
      Tag name without namespace prefix.
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _children(parent: ET.Element, tag: str) -> list[ET.Element]:
    """Finds all child elements with a given tag name.

    Args:
      parent: Parent XML element.
      tag: Tag name to search for (namespace prefixes are ignored).

    Returns:
      List of matching child elements.
    """
    return [child for child in parent if _strip_ns(child.tag) == tag]


def _first_child(parent: ET.Element, tag: str) -> ET.Element | None:
    """Finds the first child element with a given tag name.

    Args:
      parent: Parent XML element.
      tag: Tag name to search for (namespace prefixes are ignored).

    Returns:
      First matching child element, or None if not found.
    """
    for child in parent:
        if _strip_ns(child.tag) == tag:
            return child
    return None


def _set_attr(target: dict[str, Any], element: ET.Element, attr: str) -> None:
    """Sets an attribute from XML element to target dict if present and non-empty.

    Args:
      target: Dictionary to update.
      element: XML element to read attribute from.
      attr: Attribute name to read.
    """
    if attr in element.attrib:
        value = element.attrib[attr]
        if value != "":
            target[attr] = value


def _set_bool_attr(target: dict[str, Any], element: ET.Element, attr: str) -> None:
    """Sets a boolean attribute from XML element to target dict.

    Converts "true"/"false" strings to boolean values.

    Args:
      target: Dictionary to update.
      element: XML element to read attribute from.
      attr: Attribute name to read.
    """
    if attr in element.attrib:
        value = element.attrib[attr].strip().lower()
        if value in {"true", "false"}:
            target[attr] = value == "true"


def _set_int_attr(target: dict[str, Any], element: ET.Element, attr: str) -> None:
    """Sets an integer attribute from XML element to target dict.

    Attempts to parse the attribute value as an integer. Falls back to string
    if parsing fails.

    Args:
      target: Dictionary to update.
      element: XML element to read attribute from.
      attr: Attribute name to read.
    """
    if attr in element.attrib:
        raw = element.attrib[attr].strip()
        if raw == "":
            return
        try:
            target[attr] = int(raw)
        except ValueError:
            target[attr] = raw
