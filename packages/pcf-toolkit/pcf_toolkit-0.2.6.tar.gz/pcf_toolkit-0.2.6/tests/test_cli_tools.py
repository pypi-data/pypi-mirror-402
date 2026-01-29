"""CLI integration tests for the manifest toolkit."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from typer.testing import CliRunner

from pcf_toolkit.cli import app
from pcf_toolkit.models import Manifest
from pcf_toolkit.xml import ManifestXmlSerializer
from pcf_toolkit.xml_import import parse_manifest_xml_text

runner = CliRunner()


def _minimal_manifest_dict() -> dict[str, object]:
    return {
        "control": {
            "namespace": "Sample",
            "constructor": "SampleControl",
            "version": "1.0.0",
            "display-name-key": "Sample_Display",
            "control-type": "virtual",
            "resources": {
                "code": {"path": "index.ts", "order": 1},
            },
        }
    }


def _write_yaml(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=False,
        ),
        encoding="utf-8",
    )


def _write_xml(path: Path, xml_text: str) -> None:
    path.write_text(xml_text, encoding="utf-8")


def test_cli_validate_and_generate(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    _write_yaml(manifest_path, _minimal_manifest_dict())

    result = runner.invoke(app, ["validate", str(manifest_path)])
    assert result.exit_code == 0
    assert "Manifest is valid" in result.output

    xml_path = tmp_path / "ControlManifest.Input.xml"
    result = runner.invoke(app, ["generate", str(manifest_path), "-o", str(xml_path)])
    assert result.exit_code == 0
    assert xml_path.exists()
    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    assert root.tag == "manifest"
    control_el = root.find("control")
    assert control_el is not None
    assert control_el.attrib.get("control-type") == "virtual"


def test_cli_validate_from_stdin() -> None:
    result = runner.invoke(
        app,
        ["validate", "-"],
        input=yaml.safe_dump(_minimal_manifest_dict(), sort_keys=False),
    )
    assert result.exit_code == 0
    assert "Manifest is valid" in result.output


def test_cli_validate_failure() -> None:
    invalid = {"control": {"namespace": "Bad", "constructor": "Control"}}
    result = runner.invoke(app, ["validate", "-"], input=yaml.safe_dump(invalid))
    assert result.exit_code != 0
    assert "Manifest is invalid" in result.output


def test_cli_validate_json_file(tmp_path: Path) -> None:
    json_path = tmp_path / "manifest.json"
    json_path.write_text(json.dumps(_minimal_manifest_dict()), encoding="utf-8")
    result = runner.invoke(app, ["validate", str(json_path)])
    assert result.exit_code == 0


def test_cli_import_xml_to_yaml_and_json(tmp_path: Path) -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display" '
        'control-type="virtual">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    xml_path = tmp_path / "ControlManifest.Input.xml"
    _write_xml(xml_path, xml_text)

    yaml_path = tmp_path / "manifest.yaml"
    result = runner.invoke(app, ["import-xml", str(xml_path), "-o", str(yaml_path)])
    assert result.exit_code == 0
    yaml_text = yaml_path.read_text(encoding="utf-8")
    assert yaml_text.splitlines()[0].startswith("# yaml-language-server:")
    data = yaml.safe_load(yaml_text)
    assert data["control"]["control-type"] == "virtual"

    json_path = tmp_path / "manifest.json"
    result = runner.invoke(app, ["import-xml", str(xml_path), "--format", "json", "-o", str(json_path)])
    assert result.exit_code == 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["$schema"].startswith("https://raw.githubusercontent.com/")
    assert data["control"]["control-type"] == "virtual"

    no_schema_path = tmp_path / "manifest-no-schema.yaml"
    result = runner.invoke(
        app,
        [
            "import-xml",
            str(xml_path),
            "--no-schema-directive",
            "-o",
            str(no_schema_path),
        ],
    )
    assert result.exit_code == 0
    assert not no_schema_path.read_text(encoding="utf-8").startswith("# yaml-language-server:")


def test_cli_import_xml_from_stdin(tmp_path: Path) -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display" '
        'control-type="virtual">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    out_path = tmp_path / "manifest.yaml"
    result = runner.invoke(app, ["import-xml", "-", "-o", str(out_path)], input=xml_text)
    assert result.exit_code == 0
    data = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert data["control"]["control-type"] == "virtual"


def test_cli_import_xml_invalid_root(tmp_path: Path) -> None:
    xml_text = "<notmanifest />"
    xml_path = tmp_path / "broken.xml"
    _write_xml(xml_path, xml_text)
    result = runner.invoke(app, ["import-xml", str(xml_path)])
    assert result.exit_code != 0
    assert "Import failed" in result.output


def test_cli_import_xml_validation_error(tmp_path: Path) -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" version="1.0.0" display-name-key="Sample_Display">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    xml_path = tmp_path / "ControlManifest.Input.xml"
    _write_xml(xml_path, xml_text)
    result = runner.invoke(app, ["import-xml", str(xml_path)])
    assert result.exit_code != 0
    assert "Manifest is invalid" in result.output


def test_cli_import_xml_no_validate_stdout(tmp_path: Path) -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    xml_path = tmp_path / "ControlManifest.Input.xml"
    _write_xml(xml_path, xml_text)
    result = runner.invoke(app, ["import-xml", str(xml_path), "--no-validate"])
    assert result.exit_code == 0
    assert "control:" in result.output


def test_cli_generate_from_stdin() -> None:
    yaml_text = yaml.safe_dump(_minimal_manifest_dict(), sort_keys=False)
    result = runner.invoke(app, ["generate", "-"], input=yaml_text)
    assert result.exit_code == 0
    assert "<manifest" in result.output


def test_cli_generate_no_declaration(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    _write_yaml(manifest_path, _minimal_manifest_dict())
    result = runner.invoke(app, ["generate", str(manifest_path), "--no-declaration"])
    assert result.exit_code == 0
    assert not result.output.lstrip().startswith("<?xml")


def test_cli_generate_from_json_file(tmp_path: Path) -> None:
    json_path = tmp_path / "manifest.json"
    json_path.write_text(json.dumps(_minimal_manifest_dict()), encoding="utf-8")
    result = runner.invoke(app, ["generate", str(json_path)])
    assert result.exit_code == 0
    assert "<manifest" in result.output


def test_cli_exports_schema_files(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    result = runner.invoke(app, ["export-json-schema", "-o", str(schema_path)])
    assert result.exit_code == 0
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "$schema" in schema
    assert "properties" in schema

    snapshot_path = tmp_path / "snapshot.json"
    result = runner.invoke(app, ["export-schema", "-o", str(snapshot_path)])
    assert result.exit_code == 0
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert "elements" in snapshot
    assert "slugs" in snapshot


def test_cli_export_schema_stdout() -> None:
    result = runner.invoke(app, ["export-schema"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "elements" in data


def test_cli_export_json_schema_stdout() -> None:
    result = runner.invoke(app, ["export-json-schema"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "$schema" in data


def test_manifest_yaml_json_roundtrip(tmp_path: Path) -> None:
    data = _minimal_manifest_dict()
    yaml_path = tmp_path / "manifest.yaml"
    json_path = tmp_path / "manifest.json"
    _write_yaml(yaml_path, data)
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    manifest_from_yaml = Manifest.model_validate(yaml.safe_load(yaml_path.read_text()))
    manifest_from_json = Manifest.model_validate(json.loads(json_path.read_text(encoding="utf-8")))

    assert manifest_from_yaml.model_dump(mode="json") == manifest_from_json.model_dump(mode="json")


def test_manifest_xml_roundtrip() -> None:
    data = _minimal_manifest_dict()
    manifest = Manifest.model_validate(data)
    xml_text = ManifestXmlSerializer(xml_declaration=False).to_string(manifest)
    parsed = parse_manifest_xml_text(xml_text)
    roundtrip = Manifest.model_validate(parsed)
    assert manifest.model_dump(mode="json") == roundtrip.model_dump(mode="json")


def test_cli_examples_command() -> None:
    result = runner.invoke(app, ["examples"])
    assert result.exit_code == 0


def test_cli_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0


def test_cli_examples_without_rich(monkeypatch) -> None:
    monkeypatch.setattr("pcf_toolkit.cli.rich_console", lambda stderr=False: None)
    result = runner.invoke(app, ["examples"])
    assert result.exit_code == 0
    assert "Examples are best viewed" in result.output


def test_cli_doctor_without_rich(monkeypatch) -> None:
    monkeypatch.setattr("pcf_toolkit.cli.rich_console", lambda stderr=False: None)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0


def test_cli_import_xml_format_validation(tmp_path: Path) -> None:
    xml_text = (
        "<manifest>"
        '<control namespace="Sample" constructor="SampleControl" '
        'version="1.0.0" display-name-key="Sample_Display">'
        '<resources><code path="index.ts" order="1" /></resources>'
        "</control>"
        "</manifest>"
    )
    xml_path = tmp_path / "ControlManifest.Input.xml"
    _write_xml(xml_path, xml_text)
    result = runner.invoke(app, ["import-xml", str(xml_path), "--format", "toml"])
    assert result.exit_code != 0


def test_cli_help_and_version() -> None:
    help_result = runner.invoke(app, ["--help"])
    assert help_result.exit_code == 0
    assert "Examples" in help_result.output
    version_result = runner.invoke(app, ["--version"])
    assert version_result.exit_code == 0
    assert "pcf-toolkit" in version_result.output


def test_cli_command_help() -> None:
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a manifest" in result.output


def test_cli_missing_path_errors() -> None:
    result = runner.invoke(app, ["validate", "missing.yaml"])
    assert result.exit_code != 0
    assert "File does not exist" in result.output
