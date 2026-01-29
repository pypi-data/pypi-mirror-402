"""Load manifest definitions from JSON or YAML."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from pcf_toolkit.models import Manifest


def load_manifest(path: str) -> Manifest:
    """Loads a manifest definition from JSON or YAML.

    Args:
      path: Path to the input file, or '-' to read from stdin.

    Returns:
      A validated Manifest instance.

    Raises:
      ValidationError: If the manifest data is invalid.
    """
    data = _load_data(path)
    return Manifest.model_validate(data)


def _load_data(path: str) -> dict[str, Any]:
    """Loads raw data from a file or stdin.

    Args:
      path: Path to the input file, or '-' to read from stdin.

    Returns:
      Parsed dictionary data from JSON or YAML.
    """
    if path == "-":
        raw = sys.stdin.read()
        return _loads_by_content(raw)

    file_path = Path(path)
    raw = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(raw)
    if file_path.suffix.lower() == ".json":
        return json.loads(raw)
    return _loads_by_content(raw)


def _loads_by_content(raw: str) -> dict[str, Any]:
    """Parses raw string content as JSON or YAML based on content.

    Args:
      raw: Raw string content to parse.

    Returns:
      Parsed dictionary data.
    """
    stripped = raw.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(raw)
    return yaml.safe_load(raw)
