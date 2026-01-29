"""Proxy configuration schema and helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_CONFIG_FILENAMES = ("pcf-proxy.yaml", "pcf-proxy.yml", "pcf-proxy.json")


class ProxyEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8080)


class HttpServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8082)


class BundleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dist_path: str = Field(
        default="out/controls/{PCF_NAME}",
        description="Relative path to the built control output.",
    )


class BrowserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prefer: str | None = Field(default="chrome", description="Preferred browser: chrome or edge.")
    path: Path | None = Field(default=None, description="Explicit browser executable path.")


class MitmproxyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: Path | None = Field(default=None, description="Explicit mitmproxy/mitmdump executable path.")


class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Environment name from PAC CLI.")
    url: str = Field(description="Environment URL.")
    active: bool = Field(default=False, description="Active PAC environment.")


class ProxyConfig(BaseModel):
    """Configuration for the PCF proxy workflow."""

    model_config = ConfigDict(extra="forbid")

    project_root: str | None = Field(
        default=None,
        description="Project root path for global configs.",
    )
    crm_url: str | None = Field(default=None, description="Base CRM URL, e.g. https://yourorg.crm.dynamics.com/")
    expected_path: str = Field(
        default="/webresources/{PCF_NAME}/",
        description="Request path template that matches the PCF webresource base.",
    )
    proxy: ProxyEndpoint = Field(default_factory=ProxyEndpoint)
    http_server: HttpServerConfig = Field(default_factory=HttpServerConfig)
    bundle: BundleConfig = Field(default_factory=BundleConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    mitmproxy: MitmproxyConfig = Field(default_factory=MitmproxyConfig)
    environments: list[EnvironmentConfig] | None = Field(
        default=None,
        description="Known CRM environments for selection.",
    )
    open_browser: bool = Field(default=True)
    auto_install: bool = Field(default=True)

    @model_validator(mode="before")
    @classmethod
    def _migrate_flat_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        data.pop("$schema", None)
        if "proxy" in data or "http_server" in data or "bundle" in data:
            return data
        migrated = dict(data)
        proxy = {"host": migrated.pop("proxy_host", None), "port": migrated.pop("proxy_port", None)}
        http_server = {
            "host": migrated.pop("http_host", None),
            "port": migrated.pop("http_port", None),
        }
        bundle = {"dist_path": migrated.pop("dist_path", None)}
        browser = {
            "prefer": migrated.pop("browser", None),
            "path": migrated.pop("browser_path", None),
        }
        mitmproxy = {"path": migrated.pop("mitmproxy_path", None)}
        migrated["proxy"] = {k: v for k, v in proxy.items() if v is not None}
        migrated["http_server"] = {k: v for k, v in http_server.items() if v is not None}
        migrated["bundle"] = {k: v for k, v in bundle.items() if v is not None}
        migrated["browser"] = {k: v for k, v in browser.items() if v is not None}
        migrated["mitmproxy"] = {k: v for k, v in mitmproxy.items() if v is not None}
        return migrated


class LoadedConfig(BaseModel):
    """Configuration plus metadata about where it came from."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    config: ProxyConfig


def global_config_path() -> Path:
    """Returns the path to the global proxy config file.

    Returns:
      Path to ~/.pcf-toolkit/pcf-proxy.yaml.
    """
    return Path.home() / ".pcf-toolkit" / "pcf-proxy.yaml"


def default_config_path(cwd: Path | None = None) -> Path:
    """Returns the default config path for the current directory.

    Searches for existing config files first, otherwise returns the default name.

    Args:
      cwd: Current working directory. If None, uses Path.cwd().

    Returns:
      Path to the config file (existing or default).
    """
    root = cwd or Path.cwd()
    for filename in DEFAULT_CONFIG_FILENAMES:
        candidate = root / filename
        if candidate.exists():
            return candidate
    return root / DEFAULT_CONFIG_FILENAMES[0]


def load_config(path: Path | None = None, cwd: Path | None = None) -> LoadedConfig:
    """Loads proxy configuration from a file.

    Tries the specified path, then local config, then global config.

    Args:
      path: Explicit config file path. If None, searches for local config.
      cwd: Current working directory for local config search.

    Returns:
      LoadedConfig instance with config and path metadata.

    Raises:
      FileNotFoundError: If no config file can be found.
    """
    resolved_path = path or default_config_path(cwd)
    if not resolved_path.exists():
        global_path = global_config_path()
        if global_path.exists():
            resolved_path = global_path
    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")
    content = resolved_path.read_text(encoding="utf-8").strip()
    data: dict[str, Any]
    if not content:
        data = {}
    elif resolved_path.suffix.lower() == ".json":
        data = _load_json(content)
    else:
        data = _load_yaml(content)
    return LoadedConfig(path=resolved_path, config=ProxyConfig.model_validate(data))


def write_default_config(
    path: Path,
    overwrite: bool = False,
    header_comment: list[str] | None = None,
) -> Path:
    """Writes a default proxy configuration file.

    Args:
      path: File path to write the config to.
      overwrite: If True, overwrites existing file.
      header_comment: Optional list of comment lines to include in header.

    Returns:
      The path where the config was written.

    Raises:
      FileExistsError: If file exists and overwrite is False.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(f"Config file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    config = ProxyConfig(
        crm_url="https://yourorg.crm.dynamics.com/",
        expected_path="/webresources/{PCF_NAME}/",
        proxy=ProxyEndpoint(host="127.0.0.1", port=8080),
        http_server=HttpServerConfig(host="127.0.0.1", port=8082),
        bundle=BundleConfig(dist_path="out/controls/{PCF_NAME}"),
        browser=BrowserConfig(prefer="chrome"),
        mitmproxy=MitmproxyConfig(path=None),
        open_browser=True,
        auto_install=True,
    )
    schema_url = (
        "https://raw.githubusercontent.com/vectorfy-co/pcf-toolkit/refs/heads/main/schemas/pcf-proxy.schema.json"
    )
    payload = config.model_dump()
    if path.suffix.lower() == ".json":
        if "$schema" not in payload:
            payload = {"$schema": schema_url, **payload}
        text = _dump_json(payload)
    else:
        text = _dump_yaml(payload)
        header_lines = [f"# yaml-language-server: $schema={schema_url}"]
        if header_comment:
            header_lines.extend(f"# {line}" for line in header_comment if line)
        text = "\n".join(header_lines) + "\n" + text
    path.write_text(text, encoding="utf-8")
    return path


def render_dist_path(config: ProxyConfig, component: str, root: Path) -> Path:
    """Renders the dist path template with component name.

    Args:
      config: Proxy configuration containing dist_path template.
      component: PCF component name to substitute.
      root: Project root directory.

    Returns:
      Resolved Path object for the component's dist directory.
    """
    relative = config.bundle.dist_path.replace("{PCF_NAME}", component)
    return root / relative


def _load_json(content: str) -> dict[str, Any]:
    """Loads JSON content into a dictionary.

    Args:
      content: JSON string to parse.

    Returns:
      Parsed dictionary data.
    """
    import json

    return json.loads(content)


def _load_yaml(content: str) -> dict[str, Any]:
    """Loads YAML content into a dictionary.

    Args:
      content: YAML string to parse.

    Returns:
      Parsed dictionary data.

    Raises:
      ValueError: If content is not a mapping.
    """
    data = yaml.safe_load(content)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Config file must be a mapping")
    return data


def _dump_json(data: dict[str, Any]) -> str:
    """Serializes dictionary to JSON string.

    Args:
      data: Dictionary to serialize.

    Returns:
      Formatted JSON string with newline.
    """
    import json

    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _dump_yaml(data: dict[str, Any]) -> str:
    """Serializes dictionary to YAML string.

    Args:
      data: Dictionary to serialize.

    Returns:
      Formatted YAML string.
    """
    return yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
