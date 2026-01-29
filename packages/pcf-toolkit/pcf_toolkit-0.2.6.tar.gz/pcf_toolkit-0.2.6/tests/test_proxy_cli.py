"""Tests for the proxy CLI workflow."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from pcf_toolkit.cli import app
from pcf_toolkit.proxy.cli import (
    _detect_component_names,
    _parse_pac_auth_list,
    _patch_bundle_dist_path,
    _patch_environments,
    _patch_mitmproxy_path,
)
from pcf_toolkit.proxy.config import (
    EnvironmentConfig,
    ProxyConfig,
    default_config_path,
    load_config,
    render_dist_path,
    write_default_config,
)

runner = CliRunner()


class _DummyProc:
    def __init__(self, pid: int = 0) -> None:
        self.pid = pid


def test_proxy_config_roundtrip(tmp_path: Path) -> None:
    config_path = tmp_path / "pcf-proxy.yaml"
    write_default_config(config_path, overwrite=True)
    loaded = load_config(config_path)
    assert loaded.config.proxy.port == 8080
    assert "crm.dynamics.com" in (loaded.config.crm_url or "")

    dist = render_dist_path(loaded.config, "MyControl", tmp_path)
    assert dist == tmp_path / "out" / "controls" / "MyControl"


def test_default_config_path_prefers_existing(tmp_path: Path) -> None:
    existing = tmp_path / "pcf-proxy.yml"
    existing.write_text("{}", encoding="utf-8")
    resolved = default_config_path(tmp_path)
    assert resolved == existing


def test_proxy_init_adds_config_and_script(tmp_path: Path, monkeypatch) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text(json.dumps({"name": "demo"}), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["proxy", "init"])

    assert result.exit_code == 0
    config_path = tmp_path / "pcf-proxy.yaml"
    assert config_path.exists()
    pkg = json.loads(package_json.read_text(encoding="utf-8"))
    # No component manifest, so uses 'auto' for runtime detection
    assert pkg["scripts"]["dev:proxy"] == "uvx pcf-toolkit proxy start auto"


def test_proxy_init_adds_script_with_detected_component(tmp_path: Path, monkeypatch) -> None:
    """Test that init detects component name and includes it in npm script."""
    package_json = tmp_path / "package.json"
    package_json.write_text(json.dumps({"name": "demo"}), encoding="utf-8")

    # Create a ControlManifest.Input.xml with a component name
    xml_path = tmp_path / "ControlManifest.Input.xml"
    xml_path.write_text(
        '<manifest><control namespace="Contoso" constructor="MyWidget" /></manifest>',
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["proxy", "init"])

    assert result.exit_code == 0
    pkg = json.loads(package_json.read_text(encoding="utf-8"))
    # Should use detected component name (namespace.constructor)
    assert pkg["scripts"]["dev:proxy"] == "uvx pcf-toolkit proxy start Contoso.MyWidget"


def test_proxy_start_and_stop(tmp_path: Path, monkeypatch) -> None:
    component = "MyControl"
    dist_dir = tmp_path / "out" / "controls" / component
    dist_dir.mkdir(parents=True)

    config = ProxyConfig(
        crm_url="https://example.crm.dynamics.com/",
        expected_path="/webresources/{PCF_NAME}/",
        open_browser=False,
        auto_install=True,
    )
    config_path = tmp_path / "pcf-proxy.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")

    monkeypatch.setattr("pcf_toolkit.proxy.cli.ensure_mitmproxy", lambda *args, **kwargs: Path("mitmdump"))
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_http_server", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_mitmproxy", lambda *args, **kwargs: _DummyProc())

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "proxy",
            "start",
            component,
            "--detach",
            "--no-open-browser",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    session_file = tmp_path / ".pcf-toolkit" / "proxy.session.json"
    assert session_file.exists()

    stop_result = runner.invoke(app, ["proxy", "stop"])

    assert stop_result.exit_code == 0
    assert not session_file.exists()


def test_proxy_init_global_sets_project_root(tmp_path: Path, monkeypatch) -> None:
    global_path = tmp_path / "global" / "pcf-proxy.yaml"
    monkeypatch.setattr("pcf_toolkit.proxy.cli.global_config_path", lambda: global_path)
    monkeypatch.setattr("pcf_toolkit.proxy.config.global_config_path", lambda: global_path)

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["proxy", "init", "--global", "--no-interactive"])

    assert result.exit_code == 0
    data = yaml.safe_load(global_path.read_text(encoding="utf-8"))
    assert data["project_root"] == str(tmp_path)


def test_proxy_start_uses_global_project_root(tmp_path: Path, monkeypatch) -> None:
    global_path = tmp_path / "global" / "pcf-proxy.yaml"
    project_root = tmp_path / "project"
    component = "MyControl"
    dist_dir = project_root / "out" / "controls" / component
    dist_dir.mkdir(parents=True)

    config = ProxyConfig(
        crm_url="https://example.crm.dynamics.com/",
        expected_path="/webresources/{PCF_NAME}/",
        open_browser=False,
        auto_install=True,
        project_root=str(project_root),
    )
    global_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")

    monkeypatch.setattr("pcf_toolkit.proxy.cli.global_config_path", lambda: global_path)
    monkeypatch.setattr("pcf_toolkit.proxy.config.global_config_path", lambda: global_path)
    monkeypatch.setattr("pcf_toolkit.proxy.cli.ensure_mitmproxy", lambda *args, **kwargs: Path("mitmdump"))
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_http_server", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_mitmproxy", lambda *args, **kwargs: _DummyProc())

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["proxy", "start", component, "--detach"])

    assert result.exit_code == 0
    session_file = project_root / ".pcf-toolkit" / "proxy.session.json"
    assert session_file.exists()


def test_proxy_start_prefers_explicit_root(tmp_path: Path, monkeypatch) -> None:
    global_path = tmp_path / "global" / "pcf-proxy.yaml"
    project_root = tmp_path / "project"
    explicit_root = tmp_path / "explicit"
    component = "MyControl"
    dist_dir = explicit_root / "out" / "controls" / component
    dist_dir.mkdir(parents=True)

    config = ProxyConfig(
        crm_url="https://example.crm.dynamics.com/",
        expected_path="/webresources/{PCF_NAME}/",
        open_browser=False,
        auto_install=True,
        project_root=str(project_root),
    )
    global_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")

    monkeypatch.setattr("pcf_toolkit.proxy.cli.global_config_path", lambda: global_path)
    monkeypatch.setattr("pcf_toolkit.proxy.config.global_config_path", lambda: global_path)
    monkeypatch.setattr("pcf_toolkit.proxy.cli.ensure_mitmproxy", lambda *args, **kwargs: Path("mitmdump"))
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_http_server", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_mitmproxy", lambda *args, **kwargs: _DummyProc())

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["proxy", "start", component, "--detach", "--root", str(explicit_root)],
    )

    assert result.exit_code == 0
    session_file = explicit_root / ".pcf-toolkit" / "proxy.session.json"
    assert session_file.exists()


def test_detect_component_names_from_xml(tmp_path: Path) -> None:
    xml_path = tmp_path / "ControlManifest.Input.xml"
    xml_path.write_text(
        '<manifest><control namespace="Demo" constructor="Widget" /></manifest>',
        encoding="utf-8",
    )
    candidates = _detect_component_names(tmp_path)
    assert "Demo.Widget" in candidates
    assert "Widget" in candidates


def test_patch_bundle_dist_path_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "pcf-proxy.yaml"
    write_default_config(config_path, overwrite=True)
    _patch_bundle_dist_path(config_path, "dist/controls/{PCF_NAME}")
    text = config_path.read_text(encoding="utf-8")
    assert "dist_path:" in text
    assert "dist/controls/{PCF_NAME}" in text


def test_patch_mitmproxy_path_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "pcf-proxy.yaml"
    write_default_config(config_path, overwrite=True)
    _patch_mitmproxy_path(config_path, Path("/opt/mitmproxy"))
    text = config_path.read_text(encoding="utf-8")
    assert "mitmproxy:" in text
    assert "/opt/mitmproxy" in text


def test_patch_environments_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "pcf-proxy.yaml"
    write_default_config(config_path, overwrite=True)
    envs = [
        EnvironmentConfig(name="Dev", url="https://dev.crm.dynamics.com/", active=True),
        EnvironmentConfig(name="Prod", url="https://prod.crm.dynamics.com/", active=False),
    ]
    _patch_environments(config_path, envs)
    text = config_path.read_text(encoding="utf-8")
    assert "environments:" in text
    assert "Dev" in text
    assert "prod.crm.dynamics.com" in text


def test_proxy_start_selects_env_by_name(tmp_path: Path, monkeypatch) -> None:
    component = "MyControl"
    dist_dir = tmp_path / "out" / "controls" / component
    dist_dir.mkdir(parents=True)
    envs = [
        EnvironmentConfig(name="Dev", url="https://dev.crm.dynamics.com/", active=False),
        EnvironmentConfig(name="Prod", url="https://prod.crm.dynamics.com/", active=True),
    ]
    config = ProxyConfig(
        crm_url=None,
        expected_path="/webresources/{PCF_NAME}/",
        open_browser=True,
        auto_install=True,
        environments=envs,
    )
    config_path = tmp_path / "pcf-proxy.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")

    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "pcf_toolkit.proxy.cli.ensure_mitmproxy",
        lambda *args, **kwargs: Path("mitmdump"),
    )
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_http_server", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_mitmproxy", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr(
        "pcf_toolkit.proxy.cli.find_browser_binary",
        lambda *args, **kwargs: Path("browser"),
    )

    def _capture_launch(_binary, url, *_args, **_kwargs):
        captured["url"] = url

    monkeypatch.setattr("pcf_toolkit.proxy.cli.launch_browser", _capture_launch)

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "proxy",
            "start",
            component,
            "--detach",
            "--env",
            "Dev",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["url"] == "https://dev.crm.dynamics.com/"


def test_proxy_start_uses_active_env_when_not_interactive(tmp_path: Path, monkeypatch) -> None:
    component = "MyControl"
    dist_dir = tmp_path / "out" / "controls" / component
    dist_dir.mkdir(parents=True)
    envs = [
        EnvironmentConfig(name="Dev", url="https://dev.crm.dynamics.com/", active=False),
        EnvironmentConfig(name="Prod", url="https://prod.crm.dynamics.com/", active=True),
    ]
    config = ProxyConfig(
        crm_url=None,
        expected_path="/webresources/{PCF_NAME}/",
        open_browser=True,
        auto_install=True,
        environments=envs,
    )
    config_path = tmp_path / "pcf-proxy.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")

    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "pcf_toolkit.proxy.cli.ensure_mitmproxy",
        lambda *args, **kwargs: Path("mitmdump"),
    )
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_http_server", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr("pcf_toolkit.proxy.cli.spawn_mitmproxy", lambda *args, **kwargs: _DummyProc())
    monkeypatch.setattr(
        "pcf_toolkit.proxy.cli.find_browser_binary",
        lambda *args, **kwargs: Path("browser"),
    )

    def _capture_launch(_binary, url, *_args, **_kwargs):
        captured["url"] = url

    monkeypatch.setattr("pcf_toolkit.proxy.cli.launch_browser", _capture_launch)

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "proxy",
            "start",
            component,
            "--detach",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["url"] == "https://prod.crm.dynamics.com/"


def test_parse_pac_auth_list() -> None:
    sample = (
        "Index Active Kind      Name User                          Cloud  Type Environment       Environment Url\n"
        "[1]          UNIVERSAL      user@example.com              Public User env-prod           https://example.crm.dynamics.com/\n"
        "[2]   *      UNIVERSAL      user@example.com              Public User env-dev            https://dev.crm.dynamics.com/\n"
    )
    entries = _parse_pac_auth_list(sample)
    assert len(entries) == 2
    assert entries[1][2] is True
    assert entries[1][1] == "https://dev.crm.dynamics.com/"
