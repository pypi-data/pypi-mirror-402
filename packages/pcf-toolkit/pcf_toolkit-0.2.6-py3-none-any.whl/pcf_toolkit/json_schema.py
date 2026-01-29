"""Generate JSON Schema for PCF manifest YAML/JSON validation."""

from __future__ import annotations

import json
from typing import Any

from pcf_toolkit.models import Manifest

JSON_SCHEMA_URL = "https://json-schema.org/draft/2020-12/schema"


def manifest_schema() -> dict[str, Any]:
    """Returns the JSON Schema for the manifest model.

    Returns:
      A dictionary containing the JSON Schema with $schema field set.
    """
    schema = Manifest.model_json_schema(by_alias=True)
    schema["$schema"] = JSON_SCHEMA_URL
    return schema


def manifest_schema_text() -> str:
    """Returns the JSON Schema as pretty-printed JSON string.

    Returns:
      A formatted JSON string representation of the schema.
    """
    return json.dumps(manifest_schema(), indent=2, ensure_ascii=True)
