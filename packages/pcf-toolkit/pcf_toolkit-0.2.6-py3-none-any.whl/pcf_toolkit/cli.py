"""CLI entrypoints for the PCF toolkit."""

from __future__ import annotations

import json
import sys
import textwrap
from importlib import metadata
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from pcf_toolkit.cli_helpers import render_validation_table, rich_console
from pcf_toolkit.io import load_manifest
from pcf_toolkit.json_schema import manifest_schema_text
from pcf_toolkit.proxy.cli import app as proxy_app
from pcf_toolkit.rich_help import RichTyperCommand, RichTyperGroup
from pcf_toolkit.schema_snapshot import load_schema_snapshot
from pcf_toolkit.xml import ManifestXmlSerializer
from pcf_toolkit.xml_import import parse_manifest_xml_path

APP_HELP = textwrap.dedent(
    """
    [bold]PCF toolkit[/bold]

    Author [i]ControlManifest.Input.xml[/i] as code.
    Validate with strong typing.
    Generate deterministic XML.
    Proxy PCF webresources for local dev.
    """
).strip()

APP_EPILOG = textwrap.dedent(
    """
    [bold cyan]Examples[/bold cyan]

      - pcf-toolkit validate manifest.yaml

      - pcf-toolkit generate manifest.yaml -o ControlManifest.Input.xml

      - pcf-toolkit proxy start MyComponent

      - pcf-toolkit export-json-schema -o schemas/pcf-manifest.schema.json

    [bold cyan]Tips[/bold cyan]

      - Install shell completion: pcf-toolkit --install-completion

      - Use YAML schema validation:

        # yaml-language-server: $schema=https://raw.githubusercontent.com/vectorfy-co/pcf-toolkit/refs/heads/main/schemas/pcf-manifest.schema.json
    """
).strip()


def _version_callback(value: bool) -> None:
    """Callback for --version option that prints version and exits.

    Args:
      value: Whether the version flag was set.
    """
    if not value:
        return
    version = metadata.version("pcf-toolkit")
    typer.echo(f"pcf-toolkit {version}")
    raise typer.Exit()


def _validate_manifest_path(value: str) -> str:
    """Validates that a manifest path exists and is a file.

    Args:
      value: Path to validate, or "-" for stdin.

    Returns:
      The validated path string.

    Raises:
      typer.BadParameter: If the path doesn't exist or is a directory.
    """
    if value == "-":
        return value
    path = Path(value)
    if not path.exists():
        raise typer.BadParameter("File does not exist.")
    if path.is_dir():
        raise typer.BadParameter("Expected a file path, got a directory.")
    return value


def _validate_xml_path(value: str) -> str:
    """Validates that an XML path exists, is a file, and has .xml extension.

    Args:
      value: Path to validate, or "-" for stdin.

    Returns:
      The validated path string.

    Raises:
      typer.BadParameter: If the path doesn't exist, is a directory, or lacks
        .xml extension.
    """
    if value == "-":
        return value
    path = Path(value)
    if not path.exists():
        raise typer.BadParameter("File does not exist.")
    if path.is_dir():
        raise typer.BadParameter("Expected a file path, got a directory.")
    if path.suffix.lower() != ".xml":
        raise typer.BadParameter("Expected a .xml file.")
    return value


def _autocomplete_xml_path(ctx: typer.Context, args: list[str], incomplete: str) -> list[str]:
    """Provides autocomplete suggestions for XML file paths.

    Args:
      ctx: Typer context (unused).
      args: Command arguments (unused).
      incomplete: The incomplete path string to complete.

    Returns:
      List of completion candidates (XML files or directories).
    """
    if incomplete == "-":
        return ["-"]
    if incomplete.startswith("-"):
        return []
    if incomplete in {"", "."}:
        base = Path(".")
        prefix = ""
    elif incomplete.endswith(("/", "\\")):
        base = Path(incomplete)
        prefix = ""
    else:
        path = Path(incomplete)
        base = path.parent if str(path.parent) else Path(".")
        prefix = path.name
    if not base.exists():
        return []
    completions: list[str] = []
    try:
        for child in base.iterdir():
            if not child.name.startswith(prefix):
                continue
            if child.is_dir():
                completions.append(f"{child}/")
            elif child.is_file() and child.suffix.lower() == ".xml":
                completions.append(str(child))
    except PermissionError:
        return []
    return completions


def _render_validation_error(exc: ValidationError) -> None:
    """Renders Pydantic validation errors in a user-friendly format.

    Args:
      exc: The ValidationError exception to render.
    """
    typer.secho("Manifest is invalid.", fg=typer.colors.RED, bold=True, err=True)
    errors = exc.errors()
    if render_validation_table(errors, title="Validation Errors", stderr=True):
        return
    for error in errors:
        loc = ".".join(str(part) for part in error.get("loc", [])) or "<root>"
        msg = error.get("msg", "Invalid value")
        error_type = error.get("type", "validation_error")
        typer.echo(f"  - {loc}: {msg} ({error_type})", err=True)
    typer.echo(
        "Tip: run 'pcf-toolkit export-json-schema' and use the schema in your editor.",
        err=True,
    )


app = typer.Typer(
    name="pcf-toolkit",
    cls=RichTyperGroup,
    help=APP_HELP,
    epilog=APP_EPILOG,
    short_help="PCF toolkit for manifests and local proxy workflows.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    suggest_commands=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.add_typer(
    proxy_app,
    name="proxy",
    help="Local dev proxy for PCF components.",
)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed version and exit.",
        is_eager=True,
        callback=_version_callback,
        rich_help_panel="Global options",
    ),
) -> None:
    """Main CLI entrypoint for the PCF toolkit."""


VALIDATE_HELP = textwrap.dedent(
    """
    Validate a manifest definition against the PCF schema.

    Supports YAML and JSON. Use '-' to read from stdin.
    """
).strip()

VALIDATE_EPILOG = textwrap.dedent(
    """
      - pcf-toolkit validate manifest.yaml

      - cat manifest.yaml | pcf-toolkit validate -
    """
).strip()


@app.command(
    "validate",
    cls=RichTyperCommand,
    help=VALIDATE_HELP,
    epilog=VALIDATE_EPILOG,
    rich_help_panel="Core commands",
)
def validate_manifest(
    path: str = typer.Argument(
        ...,
        metavar="MANIFEST",
        help="Path to a YAML/JSON manifest definition, or '-' for stdin.",
        allow_dash=True,
        callback=_validate_manifest_path,
    ),
) -> None:
    """Validates a manifest definition against the PCF schema.

    Args:
      path: Path to a YAML/JSON manifest file, or '-' to read from stdin.

    Raises:
      typer.Exit: Exit code 1 if validation fails.
    """
    try:
        load_manifest(path)
    except ValidationError as exc:
        _render_validation_error(exc)
        raise typer.Exit(code=1) from exc
    typer.secho("Manifest is valid.", fg=typer.colors.GREEN, bold=True)


GENERATE_HELP = textwrap.dedent(
    """
    Generate ControlManifest.Input.xml from a manifest definition.

    Supports YAML and JSON. Use '-' to read from stdin.
    """
).strip()

GENERATE_EPILOG = textwrap.dedent(
    """
      - pcf-toolkit generate manifest.yaml -o ControlManifest.Input.xml

      - cat manifest.yaml | pcf-toolkit generate -
    """
).strip()


@app.command(
    "generate",
    cls=RichTyperCommand,
    help=GENERATE_HELP,
    epilog=GENERATE_EPILOG,
    rich_help_panel="Core commands",
)
def generate_manifest(
    path: str = typer.Argument(
        ...,
        metavar="MANIFEST",
        help="Path to a YAML/JSON manifest definition, or '-' for stdin.",
        allow_dash=True,
        callback=_validate_manifest_path,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        metavar="FILE",
        help="Write XML to a file instead of stdout.",
        dir_okay=False,
        writable=True,
        rich_help_panel="Output",
    ),
    no_declaration: bool = typer.Option(
        False,
        "--no-declaration",
        help="Omit the XML declaration header.",
        rich_help_panel="Output",
    ),
) -> None:
    """Generates ControlManifest.Input.xml from a manifest definition.

    Args:
      path: Path to a YAML/JSON manifest file, or '-' to read from stdin.
      output: Optional file path to write XML to. If not provided, writes to
        stdout.
      no_declaration: If True, omits the XML declaration header.
    """
    manifest = load_manifest(path)
    serializer = ManifestXmlSerializer(xml_declaration=not no_declaration)
    xml_text = serializer.to_string(manifest)
    if output:
        output.write_text(xml_text, encoding="utf-8")
        typer.secho(f"Wrote {output}", fg=typer.colors.GREEN, bold=True)
        return
    typer.echo(xml_text)


IMPORT_XML_HELP = textwrap.dedent(
    """
    Convert an existing ControlManifest.Input.xml into YAML or JSON.

    The output matches the manifest schema so you can keep using YAML from now on.
    """
).strip()

IMPORT_XML_EPILOG = textwrap.dedent(
    """
      - pcf-toolkit import-xml ControlManifest.Input.xml -o manifest.yaml

      - pcf-toolkit import-xml ControlManifest.Input.xml --format json
    """
).strip()


@app.command(
    "import-xml",
    cls=RichTyperCommand,
    help=IMPORT_XML_HELP,
    epilog=IMPORT_XML_EPILOG,
    rich_help_panel="Core commands",
)
def import_xml(
    path: str = typer.Argument(
        ...,
        metavar="XML",
        help="Path to ControlManifest.Input.xml (.xml), or '-' for stdin.",
        allow_dash=True,
        callback=_validate_xml_path,
        autocompletion=_autocomplete_xml_path,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        metavar="FILE",
        help="Write YAML/JSON to a file instead of stdout.",
        dir_okay=False,
        writable=True,
        rich_help_panel="Output",
    ),
    output_format: str = typer.Option(
        "yaml",
        "--format",
        help="Output format: yaml or json.",
        rich_help_panel="Output",
    ),
    schema_directive: bool = typer.Option(
        True,
        "--schema-directive/--no-schema-directive",
        help="Include schema header when outputting YAML/JSON.",
        rich_help_panel="Output",
    ),
    schema_path: str = typer.Option(
        "https://raw.githubusercontent.com/vectorfy-co/pcf-toolkit/refs/heads/main/schemas/pcf-manifest.schema.json",
        "--schema-path",
        help="Schema path used in the YAML/JSON output.",
        rich_help_panel="Output",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate the imported manifest against the schema.",
        rich_help_panel="Validation",
    ),
) -> None:
    """Converts ControlManifest.Input.xml into YAML or JSON format.

    Args:
      path: Path to ControlManifest.Input.xml file, or '-' to read from stdin.
      output: Optional file path to write output to. If not provided, writes to
        stdout.
      output_format: Output format, either 'yaml' or 'json'.
      schema_directive: If True, includes schema directive in output.
      schema_path: URL or path to schema file for the directive.
      validate: If True, validates the imported manifest against the schema.

    Raises:
      typer.BadParameter: If output_format is not 'yaml' or 'json'.
      typer.Exit: Exit code 1 if import or validation fails.
    """
    try:
        raw = parse_manifest_xml_path(path)
    except ValueError as exc:
        typer.secho(f"Import failed: {exc}", fg=typer.colors.RED, bold=True, err=True)
        typer.echo(
            "Tip: pass a valid ControlManifest.Input.xml file, or use '-' for stdin.",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - defensive: unexpected parser issues
        typer.secho(
            f"Import failed due to an unexpected error: {exc}",
            fg=typer.colors.RED,
            bold=True,
            err=True,
        )
        typer.echo("Tip: try --format json to inspect the parsed structure.", err=True)
        raise typer.Exit(code=1) from exc

    if validate:
        from pcf_toolkit.models import Manifest

        try:
            manifest = Manifest.model_validate(raw)
        except ValidationError as exc:
            _render_validation_error(exc)
            raise typer.Exit(code=1) from exc
        data = manifest.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
            mode="json",
        )
    else:
        data = raw

    output_format = output_format.lower()
    if output_format not in {"yaml", "json"}:
        raise typer.BadParameter("format must be 'yaml' or 'json'")

    if output_format == "json":
        if schema_directive and "$schema" not in data:
            data = {"$schema": schema_path, **data}
        text = json.dumps(data, indent=2, ensure_ascii=True)
    else:
        try:
            yaml_text = yaml.safe_dump(
                data,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=False,
            )
        except Exception as exc:  # pragma: no cover - safe dump should be robust
            typer.secho(
                f"Failed to render YAML output: {exc}",
                fg=typer.colors.RED,
                bold=True,
                err=True,
            )
            typer.echo(
                "Tip: try --format json to inspect the parsed structure.",
                err=True,
            )
            raise typer.Exit(code=1) from exc
        if schema_directive:
            yaml_text = f"# yaml-language-server: $schema={schema_path}\n{yaml_text}"
        text = yaml_text

    if output:
        output.write_text(text, encoding="utf-8")
        typer.secho(f"Wrote {output}", fg=typer.colors.GREEN, bold=True)
        return
    typer.echo(text)


EXPORT_SCHEMA_HELP = textwrap.dedent(
    """
    Export the docs-derived schema snapshot used for model generation.
    """
).strip()

EXPORT_SCHEMA_EPILOG = textwrap.dedent(
    """
      - pcf-toolkit export-schema -o data/schema_snapshot.json
    """
).strip()


@app.command(
    "export-schema",
    cls=RichTyperCommand,
    help=EXPORT_SCHEMA_HELP,
    epilog=EXPORT_SCHEMA_EPILOG,
    rich_help_panel="Schema tools",
)
def export_schema(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        metavar="FILE",
        help="Write snapshot JSON to a file instead of stdout.",
        dir_okay=False,
        writable=True,
    ),
) -> None:
    """Exports the machine-readable schema snapshot JSON.

    Args:
      output: Optional file path to write schema to. If not provided, writes to
        stdout.
    """
    snapshot = load_schema_snapshot()
    if output:
        output.write_text(snapshot, encoding="utf-8")
        typer.secho(f"Wrote {output}", fg=typer.colors.GREEN, bold=True)
        return
    typer.echo(snapshot)


EXPORT_JSON_SCHEMA_HELP = textwrap.dedent(
    """
    Export JSON Schema for YAML/JSON validation.
    """
).strip()

EXPORT_JSON_SCHEMA_EPILOG = textwrap.dedent(
    """
      - pcf-toolkit export-json-schema -o schemas/pcf-manifest.schema.json
    """
).strip()


@app.command(
    "export-json-schema",
    cls=RichTyperCommand,
    help=EXPORT_JSON_SCHEMA_HELP,
    epilog=EXPORT_JSON_SCHEMA_EPILOG,
    rich_help_panel="Schema tools",
)
def export_json_schema(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        metavar="FILE",
        help="Write JSON Schema to a file instead of stdout.",
        dir_okay=False,
        writable=True,
    ),
) -> None:
    """Exports JSON Schema for manifest definitions.

    Args:
      output: Optional file path to write schema to. If not provided, writes to
        stdout.
    """
    schema_text = manifest_schema_text()
    if output:
        output.write_text(schema_text, encoding="utf-8")
        typer.secho(f"Wrote {output}", fg=typer.colors.GREEN, bold=True)
        return
    typer.echo(schema_text)


EXAMPLES_HELP = textwrap.dedent(
    """
    Show end-to-end examples for authoring and generating a manifest.
    """
).strip()


@app.command(
    "examples",
    cls=RichTyperCommand,
    help=EXAMPLES_HELP,
    rich_help_panel="Developer tools",
)
def show_examples() -> None:
    """Prints curated examples for quick start.

    Displays markdown-formatted examples showing common usage patterns.
    """
    console = rich_console(stderr=False)
    if console is None:
        typer.echo("Examples are best viewed with Rich enabled. Install extra dependencies.")
        return

    from rich.markdown import Markdown
    from rich.panel import Panel

    markdown = textwrap.dedent(
        """
        ## Validate a manifest

        ```bash
        pcf-toolkit validate manifest.yaml
        ```

        ## Generate XML

        ```bash
        pcf-toolkit generate manifest.yaml -o ControlManifest.Input.xml
        ```

        ## Import XML to YAML

        ```bash
        pcf-toolkit import-xml ControlManifest.Input.xml -o manifest.yaml
        ```

        ## Add YAML schema validation

        ```yaml
        # yaml-language-server: $schema=https://raw.githubusercontent.com/vectorfy-co/pcf-toolkit/refs/heads/main/schemas/pcf-manifest.schema.json
        ```

        ## Minimal YAML

        ```yaml
        control:
          namespace: MyNameSpace
          constructor: MyControl
          version: 1.0.0
          display-name-key: MyControl_Display_Key
          resources:
            code:
              path: index.ts
              order: 1
        ```
        """
    ).strip()
    panel = Panel(Markdown(markdown), title="Examples", title_align="left")
    console.print(panel)


DOCTOR_HELP = textwrap.dedent(
    """
    Check your environment and repository setup.
    """
).strip()


@app.command(
    "doctor",
    cls=RichTyperCommand,
    help=DOCTOR_HELP,
    rich_help_panel="Developer tools",
)
def doctor(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Return non-zero exit code on warnings.",
    ),
) -> None:
    """Inspects environment for common issues.

    Checks Python version, schema files, and other prerequisites.

    Args:
      strict: If True, returns non-zero exit code on warnings.

    Raises:
      typer.Exit: Exit code 1 if issues found (or warnings in strict mode).
    """
    console = rich_console(stderr=False)
    issues = 0
    warnings = 0

    def add_check(name: str, status: str, detail: str) -> None:
        nonlocal issues, warnings
        if status == "FAIL":
            issues += 1
        elif status == "WARN":
            warnings += 1
        if console is None:
            typer.echo(f"{status}: {name} - {detail}")
            return
        from rich.table import Table

        if not hasattr(add_check, "_table"):
            table = Table(title="Doctor", show_lines=False)
            table.add_column("Check", style="bold")
            table.add_column("Status")
            table.add_column("Details")
            add_check._table = table
        table = add_check._table
        style = {"OK": "green", "WARN": "yellow", "FAIL": "red"}.get(status, "white")
        table.add_row(name, f"[{style}]{status}[/{style}]", detail)

    # Python version
    if sys.version_info < (3, 13):
        add_check("Python", "FAIL", "Requires Python 3.13+")
    else:
        add_check("Python", "OK", f"{sys.version_info.major}.{sys.version_info.minor}")

    # Schema files
    schema_path = Path("schemas/pcf-manifest.schema.json")
    if schema_path.exists():
        add_check("JSON Schema", "OK", str(schema_path))
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            add_check("JSON Schema Parse", "FAIL", "Invalid JSON")
    else:
        add_check("JSON Schema", "WARN", "schemas/pcf-manifest.schema.json missing")

    snapshot_path = Path("data/schema_snapshot.json")
    if snapshot_path.exists():
        add_check("Schema snapshot", "OK", str(snapshot_path))
    else:
        add_check("Schema snapshot", "WARN", "data/schema_snapshot.json missing")

    packaged_schema = Path("src/pcf_toolkit/data/manifest.schema.json")
    if packaged_schema.exists():
        add_check("Packaged schema", "OK", str(packaged_schema))
    else:
        add_check("Packaged schema", "WARN", "Package schema missing")

    if console is not None and hasattr(add_check, "_table"):
        console.print(add_check._table)

    if issues or (strict and warnings):
        raise typer.Exit(code=1)
