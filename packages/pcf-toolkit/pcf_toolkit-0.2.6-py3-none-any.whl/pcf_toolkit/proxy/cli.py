"""CLI commands for the proxy workflow."""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path

import typer
import yaml

try:
    import questionary
except Exception:  # pragma: no cover - fallback when questionary isn't available
    questionary = None

try:
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except Exception:  # pragma: no cover - fallback when rich isn't available
    Panel = None
    Table = None
    Text = None

from pcf_toolkit.cli_helpers import rich_console
from pcf_toolkit.proxy.browser import find_browser_binary, launch_browser
from pcf_toolkit.proxy.config import (
    EnvironmentConfig,
    ProxyConfig,
    default_config_path,
    global_config_path,
    load_config,
    render_dist_path,
    write_default_config,
)
from pcf_toolkit.proxy.doctor import CheckResult, check_mitmproxy_certificate, run_doctor
from pcf_toolkit.proxy.mitm import ensure_mitmproxy, find_mitmproxy, spawn_mitmproxy
from pcf_toolkit.proxy.server import spawn_http_server
from pcf_toolkit.rich_help import RichTyperCommand, RichTyperGroup

app = typer.Typer(
    name="proxy",
    cls=RichTyperGroup,
    help="Local dev proxy for PCF components.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    suggest_commands=True,
)


@dataclass
class ProxySession:
    """Represents an active proxy session.

    Attributes:
      mitm_pid: Process ID of the mitmproxy process.
      http_pid: Process ID of the HTTP server process.
      proxy_port: Port number for the proxy server.
      http_port: Port number for the HTTP server.
      component: PCF component name.
      project_root: Project root directory path.
      log_path: Optional path to log file (for detached sessions).
    """

    mitm_pid: int
    http_pid: int
    proxy_port: int
    http_port: int
    component: str
    project_root: str
    log_path: str | None = None


@app.command("init", cls=RichTyperCommand, help="Create a proxy config file.")
def init(
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to the proxy config file."),
    use_global: bool = typer.Option(
        False,
        "--global",
        help="Store config in ~/.pcf-toolkit/pcf-proxy.yaml.",
    ),
    local_only: bool = typer.Option(
        False,
        "--local",
        help="Store config in the current directory.",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite the config file if it exists."),
    add_npm_script: bool = typer.Option(
        True,
        "--add-npm-script/--no-add-npm-script",
        help="Add a dev:proxy script to package.json if present.",
    ),
    npm_script_name: str = typer.Option("dev:proxy", "--npm-script", help="The npm script name to add."),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Prompt for CRM URL and dependencies.",
    ),
    crm_url: str | None = typer.Option(None, "--crm-url", help="Set CRM URL without prompting."),
    install_mitmproxy: bool | None = typer.Option(
        None,
        "--install-mitmproxy/--no-install-mitmproxy",
        help="Auto-install mitmproxy during setup.",
    ),
) -> None:
    """Creates a proxy configuration file.

    Interactive setup flow that prompts for CRM URL, dist path, and other
    settings. Can create local or global config files.

    Args:
      config_path: Explicit path to config file.
      use_global: If True, stores config in global location.
      local_only: If True, stores config in current directory.
      force: If True, overwrites existing config file.
      add_npm_script: If True, adds npm script to package.json.
      npm_script_name: Name of the npm script to add.
      interactive: If True, prompts for configuration values.
      crm_url: CRM URL to set without prompting.
      install_mitmproxy: Whether to install mitmproxy during setup.

    Raises:
      typer.BadParameter: If conflicting options are provided.
      typer.Exit: Exit code 1 if config file exists and force is False.
    """
    if use_global and local_only:
        raise typer.BadParameter("Choose either --global or --local, not both.")
    if interactive and not _is_interactive():
        interactive = False

    project_root = Path.cwd()

    # Detect component name for npm script
    component_candidates = _detect_component_names(project_root)
    detected_component: str | None = None
    if component_candidates:
        if len(component_candidates) == 1:
            detected_component = component_candidates[0]
        elif interactive and _is_interactive():
            detected_component = _prompt_select_component(component_candidates)
        else:
            detected_component = component_candidates[0]
        if detected_component:
            typer.secho(f"Detected component: {detected_component}", fg=typer.colors.CYAN)

    target_path = _resolve_init_target_path(
        config_path=config_path,
        use_global=use_global,
        local_only=local_only,
    )
    target_path = _run_init_flow(
        target_path=target_path,
        project_root=project_root,
        force=force,
        interactive=interactive,
        crm_url=crm_url,
        install_mitmproxy=install_mitmproxy,
    )
    typer.echo(f"Wrote config to {target_path}")

    if add_npm_script:
        _ensure_npm_script(project_root, npm_script_name, detected_component)


@app.command("start", cls=RichTyperCommand, help="Start the proxy workflow.")
def start(
    component: str = typer.Argument(..., help="PCF component name."),
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to the proxy config file."),
    use_global: bool = typer.Option(
        False,
        "--global",
        help="Use the global config even if a local config exists.",
    ),
    project_root: Path | None = typer.Option(
        None,
        "--root",
        help="Project root (component folder).",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    crm_url: str | None = typer.Option(None, "--crm-url", help="Override CRM URL."),
    environment: str | None = typer.Option(
        None,
        "--env",
        "--environment",
        help="Environment name or index from config.",
    ),
    proxy_port: int | None = typer.Option(None, "--proxy-port", help="Override proxy port."),
    http_port: int | None = typer.Option(None, "--http-port", help="Override HTTP server port."),
    browser: str | None = typer.Option(None, "--browser", help="Browser preference: chrome or edge."),
    browser_path: Path | None = typer.Option(None, "--browser-path", help="Explicit browser executable path."),
    mitmproxy_path: Path | None = typer.Option(None, "--mitmproxy-path", help="Explicit mitmproxy executable path."),
    dist_path: str | None = typer.Option(None, "--dist-path", help="Override dist path template."),
    open_browser: bool | None = typer.Option(
        None,
        "--open-browser/--no-open-browser",
        help="Open a browser with proxy settings.",
    ),
    auto_install: bool | None = typer.Option(
        None,
        "--auto-install/--no-auto-install",
        help="Auto-install mitmproxy if missing.",
    ),
    detach: bool = typer.Option(
        False,
        "--detach",
        help="Run the proxy in the background and return immediately.",
    ),
) -> None:
    """Starts the proxy workflow for a PCF component.

    Launches mitmproxy and HTTP server, optionally opens browser.

    Args:
      component: PCF component name (or "auto"/"select"/"detect").
      config_path: Path to proxy config file.
      use_global: If True, uses global config even if local exists.
      project_root: Project root directory.
      crm_url: Override CRM URL from config.
      environment: Environment name or index from config.
      proxy_port: Override proxy port from config.
      http_port: Override HTTP server port from config.
      browser: Browser preference (chrome or edge).
      browser_path: Explicit browser executable path.
      mitmproxy_path: Explicit mitmproxy executable path.
      dist_path: Override dist path template from config.
      open_browser: Whether to open browser automatically.
      auto_install: Whether to auto-install mitmproxy if missing.
      detach: If True, runs in background and returns immediately.

    Raises:
      typer.BadParameter: If conflicting options are provided.
      typer.Exit: Exit code 1 if config not found or dist path missing.
    """
    if use_global and config_path is not None:
        raise typer.BadParameter("Choose either --global or --config, not both.")
    if crm_url is not None and environment is not None:
        raise typer.BadParameter("Choose either --crm-url or --env, not both.")
    if use_global:
        config_path = global_config_path()

    explicit_root = project_root is not None
    project_root = (project_root or Path(".")).resolve()
    try:
        loaded = load_config(config_path, cwd=project_root)
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        _handle_missing_config(project_root, config_path)
        raise typer.Exit(code=1) from exc

    config = _apply_overrides(
        loaded.config,
        crm_url=crm_url,
        proxy_port=proxy_port,
        http_port=http_port,
        browser=browser,
        browser_path=browser_path,
        mitmproxy_path=mitmproxy_path,
        dist_path=dist_path,
        open_browser=open_browser,
        auto_install=auto_install,
    )

    selected_env = None
    if crm_url is None:
        config, selected_env = _resolve_environment(config, environment)
    if selected_env:
        typer.echo(f"Using environment: {selected_env.name} ({selected_env.url})")

    config_path_used = loaded.path
    if config_path_used == global_config_path():
        if config.project_root and not explicit_root:
            project_root = Path(config.project_root).expanduser().resolve()
            typer.echo(f"Using project root from global config: {project_root}")
        typer.echo(f"Using global config: {config_path_used}")

    if component.lower() in {"auto", "select", "detect"}:
        component = _resolve_component_name(project_root, config)
        typer.echo(f"Using component: {component}")

    dist_dir = render_dist_path(config, component, project_root)
    if not dist_dir.exists():
        lines = [
            f"Expected: {dist_dir}",
            "Run your PCF build, or update bundle.dist_path in pcf-proxy.yaml.",
        ]
        candidates = _detect_component_names(project_root)
        if candidates:
            lines.append(f"Detected control names: {', '.join(candidates)}")
            lines.append(f"Run: pcf-toolkit proxy start {candidates[0]}")
        _rich_tip("Dist path missing", lines)
        raise typer.Exit(code=1)

    try:
        mitm_binary = ensure_mitmproxy(config.auto_install, config.mitmproxy.path)
    except FileNotFoundError as exc:
        _rich_tip(
            "mitmproxy not found",
            [
                "Install it or run: pcf-toolkit proxy doctor --fix",
                "Tip: set auto_install: true in pcf-proxy.yaml",
            ],
        )
        raise typer.Exit(code=1) from exc

    session_dir = _session_dir(project_root)
    session_dir.mkdir(parents=True, exist_ok=True)
    log_file = session_dir / "proxy.log"
    stdout = None
    stderr = None
    creationflags = 0
    start_new_session = False
    log_handle = None
    if detach:
        log_handle = log_file.open("a", encoding="utf-8")
        stdout = log_handle
        stderr = log_handle
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            start_new_session = True

    with _addon_path() as addon_path:
        env = os.environ.copy()
        env.update(
            {
                "PCF_COMPONENT_NAME": component,
                "PCF_EXPECTED_PATH": config.expected_path,
                "HTTP_SERVER_PORT": str(config.http_server.port),
                "HTTP_SERVER_HOST": config.http_server.host,
            }
        )

        http_proc = spawn_http_server(
            dist_dir,
            config.http_server.host,
            config.http_server.port,
            stdout=stdout,
            stderr=stderr,
            start_new_session=start_new_session,
            creationflags=creationflags,
        )
        mitm_proc = spawn_mitmproxy(
            mitm_binary,
            addon_path,
            config.proxy.host,
            config.proxy.port,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=start_new_session,
            creationflags=creationflags,
        )

    if not detach:
        _maybe_prompt_for_cert_trust()

    if log_handle is not None:
        log_handle.close()

    if config.open_browser and config.crm_url:
        browser_binary = find_browser_binary(config.browser.prefer, config.browser.path)
        if browser_binary:
            profile_dir = session_dir / f"profile-{component}"
            launch_browser(
                browser_binary,
                config.crm_url,
                config.proxy.host,
                config.proxy.port,
                profile_dir,
            )
        else:
            typer.secho(
                "Browser not found. Set browser.path in config to auto-launch.",
                fg=typer.colors.YELLOW,
            )
    elif config.open_browser:
        typer.secho(
            "CRM URL missing. Set crm_url in config to auto-launch the browser.",
            fg=typer.colors.YELLOW,
        )

    session = ProxySession(
        mitm_pid=mitm_proc.pid,
        http_pid=http_proc.pid,
        proxy_port=config.proxy.port,
        http_port=config.http_server.port,
        component=component,
        project_root=str(project_root),
        log_path=str(log_file) if detach else None,
    )
    _write_session(session_dir, session)

    typer.secho(
        f"Proxy running for {component} on ports {config.proxy.port}/{config.http_server.port}.",
        fg=typer.colors.GREEN,
    )
    if detach:
        typer.echo(f"Detached. Logs: {log_file}")
        return

    typer.secho("Use Ctrl+C to stop.", fg=typer.colors.GREEN)

    _run_foreground(http_proc, mitm_proc, session_dir)


@app.command("stop", cls=RichTyperCommand, help="Stop a running proxy session.")
def stop(
    project_root: Path = typer.Option(
        Path("."),
        "--root",
        help="Project root used when starting the proxy.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Stops a running proxy session.

    Terminates mitmproxy and HTTP server processes.

    Args:
      project_root: Project root directory used when starting the proxy.

    Raises:
      typer.Exit: Exit code 1 if no active session found.
    """
    project_root = project_root.resolve()
    session_dir = _session_dir(project_root)
    session_file = session_dir / "proxy.session.json"
    if not session_file.exists():
        typer.secho("No active proxy session found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    session = _read_session(session_file)
    _terminate_pid(session.mitm_pid)
    _terminate_pid(session.http_pid)
    session_file.unlink(missing_ok=True)
    typer.secho("Proxy session stopped.", fg=typer.colors.GREEN)


@app.command("doctor", cls=RichTyperCommand, help="Check proxy prerequisites.")
def doctor(
    component: str | None = typer.Option(None, "--component", help="Component name to validate dist path."),
    config_path: Path | None = typer.Option(None, "--config", "-c", help="Path to the proxy config file."),
    project_root: Path = typer.Option(
        Path("."),
        "--root",
        help="Project root (component folder).",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    fix: bool = typer.Option(False, "--fix", help="Attempt safe fixes (mitmproxy install)."),
) -> None:
    """Checks proxy workflow prerequisites.

    Validates config, ports, mitmproxy, certificates, browser, and dist paths.

    Args:
      component: Component name to validate dist path.
      config_path: Path to proxy config file.
      project_root: Project root directory.
      fix: If True, attempts safe fixes (e.g., install mitmproxy).

    Raises:
      typer.Exit: Exit code 1 if checks fail.
    """
    project_root = project_root.resolve()
    config: ProxyConfig | None = None
    resolved_path = config_path or default_config_path(project_root)
    if resolved_path.exists():
        try:
            config = load_config(resolved_path, cwd=project_root).config
        except Exception as exc:  # noqa: BLE001
            typer.secho(f"Failed to read config: {exc}", fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    results = run_doctor(config, resolved_path, component, project_root)
    _print_results(results)

    if fix and config:
        _apply_fixes(results, config)

    if any(result.status == "fail" for result in results):
        raise typer.Exit(code=1)


def _apply_overrides(config: ProxyConfig, **overrides: object) -> ProxyConfig:
    """Applies command-line overrides to proxy configuration.

    Args:
      config: Base proxy configuration.
      **overrides: Keyword arguments with override values.

    Returns:
      New ProxyConfig instance with overrides applied.
    """
    update: dict[str, object] = {}
    if overrides.get("crm_url") is not None:
        update["crm_url"] = overrides["crm_url"]
    if overrides.get("proxy_port") is not None:
        update.setdefault("proxy", {})["port"] = overrides["proxy_port"]
    if overrides.get("http_port") is not None:
        update.setdefault("http_server", {})["port"] = overrides["http_port"]
    if overrides.get("browser") is not None:
        update.setdefault("browser", {})["prefer"] = overrides["browser"]
    if overrides.get("browser_path") is not None:
        update.setdefault("browser", {})["path"] = overrides["browser_path"]
    if overrides.get("mitmproxy_path") is not None:
        update.setdefault("mitmproxy", {})["path"] = overrides["mitmproxy_path"]
    if overrides.get("dist_path") is not None:
        update.setdefault("bundle", {})["dist_path"] = overrides["dist_path"]
    if overrides.get("open_browser") is not None:
        update["open_browser"] = overrides["open_browser"]
    if overrides.get("auto_install") is not None:
        update["auto_install"] = overrides["auto_install"]

    if not update:
        return config
    return config.model_copy(update=update)


def _apply_fixes(results: list[CheckResult], config: ProxyConfig) -> None:
    """Applies automatic fixes based on doctor check results.

    Args:
      results: List of check results from doctor.
      config: Proxy configuration.
    """
    for result in results:
        if result.name == "mitmproxy" and result.status == "fail":
            try:
                ensure_mitmproxy(True, config.mitmproxy.path)
                typer.secho("Installed mitmproxy.", fg=typer.colors.GREEN)
            except Exception as exc:  # noqa: BLE001
                typer.secho(f"Failed to install mitmproxy: {exc}", fg=typer.colors.RED)
        if result.name == "mitmproxy_cert" and result.status == "warn":
            if _is_interactive() and _supports_cert_install():
                if typer.confirm(
                    "Install mitmproxy CA into the system trust store? This requires sudo.",
                    default=False,
                ):
                    _install_mitmproxy_cert()
                    continue
            typer.secho(result.fix or "", fg=typer.colors.YELLOW)


def _supports_cert_install() -> bool:
    return sys.platform == "darwin" or sys.platform.startswith("linux")


def _maybe_prompt_for_cert_trust() -> None:
    cert_result = check_mitmproxy_certificate()
    if cert_result.status == "ok":
        return

    typer.secho(f"[{cert_result.status.upper()}] {cert_result.name}: {cert_result.message}", fg=typer.colors.YELLOW)
    if _is_interactive() and _supports_cert_install():
        if typer.confirm(
            "Install mitmproxy CA into the system trust store? This requires sudo.",
            default=False,
        ):
            _install_mitmproxy_cert()
            return
    if cert_result.fix:
        typer.secho(cert_result.fix, fg=typer.colors.YELLOW)


def _install_mitmproxy_cert() -> None:
    cert_path = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    if not cert_path.exists():
        typer.secho("mitmproxy CA cert not found. Run the proxy once to generate it.", fg=typer.colors.RED)
        return

    if sys.platform == "darwin":
        _run_privileged(
            [
                "sudo",
                "security",
                "add-trusted-cert",
                "-d",
                "-r",
                "trustRoot",
                "-k",
                "/Library/Keychains/System.keychain",
                str(cert_path),
            ],
            "Trusting mitmproxy CA in System Keychain...",
        )
        return

    if sys.platform.startswith("linux"):
        if shutil.which("update-ca-certificates"):
            target = Path("/usr/local/share/ca-certificates/mitmproxy-ca-cert.crt")
            _run_privileged(["sudo", "cp", str(cert_path), str(target)], "Copying cert into CA store...")
            _run_privileged(["sudo", "update-ca-certificates"], "Updating CA certificates...")
            return
        if shutil.which("update-ca-trust"):
            target = Path("/etc/pki/ca-trust/source/anchors/mitmproxy-ca-cert.pem")
            _run_privileged(["sudo", "cp", str(cert_path), str(target)], "Copying cert into CA trust anchors...")
            _run_privileged(["sudo", "update-ca-trust", "extract"], "Updating CA trust...")
            return

    typer.secho("Automatic install not supported on this platform.", fg=typer.colors.YELLOW)


def _run_privileged(command: list[str], message: str) -> None:
    typer.secho(message, fg=typer.colors.CYAN)
    try:
        subprocess.run(command, check=True)
        typer.secho("Done.", fg=typer.colors.GREEN)
    except subprocess.CalledProcessError as exc:
        typer.secho(f"Command failed: {exc}", fg=typer.colors.RED)


def _print_results(results: list[CheckResult]) -> None:
    """Prints doctor check results with color coding.

    Args:
      results: List of check results to print.
    """
    for result in results:
        if result.status == "ok":
            color = typer.colors.GREEN
        elif result.status == "warn":
            color = typer.colors.YELLOW
        else:
            color = typer.colors.RED
        typer.secho(f"[{result.status.upper()}] {result.name}: {result.message}", fg=color)
        if result.fix and result.status != "ok":
            typer.echo(f"  -> {result.fix}")


def _run_foreground(
    http_proc: subprocess.Popen,
    mitm_proc: subprocess.Popen,
    session_dir: Path,
) -> None:
    """Runs proxy processes in foreground with signal handling.

    Monitors processes and cleans up on SIGINT/SIGTERM.

    Args:
      http_proc: HTTP server process.
      mitm_proc: Mitmproxy process.
      session_dir: Session directory for cleanup.
    """

    def _shutdown(_sig, _frame) -> None:
        _terminate_proc(http_proc)
        _terminate_proc(mitm_proc)
        _clear_session(session_dir)
        raise SystemExit

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            if http_proc.poll() is not None or mitm_proc.poll() is not None:
                break
            time.sleep(0.2)
    finally:
        _terminate_proc(http_proc)
        _terminate_proc(mitm_proc)
        _clear_session(session_dir)


@contextmanager
def _addon_path():
    """Context manager providing path to mitmproxy redirect addon.

    Yields:
      Path to the redirect_bundle.py addon file.
    """
    addon = resources.files("pcf_toolkit.proxy.addons").joinpath("redirect_bundle.py")
    with resources.as_file(addon) as path:
        yield path


def _ensure_npm_script(project_root: Path, script_name: str, component: str | None = None) -> None:
    """Ensures npm script exists in package.json.

    Args:
      project_root: Project root directory.
      script_name: Name of the npm script to add.
      component: PCF component name to include in the script command.
    """
    package_json = project_root / "package.json"
    if not package_json.exists():
        typer.secho(
            "package.json not found; skipping npm script update.",
            fg=typer.colors.YELLOW,
        )
        return

    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts") or {}
    if script_name in scripts:
        typer.echo(f"npm script '{script_name}' already exists.")
        return

    # Use detected component name, or 'auto' for runtime detection
    component_arg = component or "auto"
    scripts[script_name] = f"uvx pcf-toolkit proxy start {component_arg}"
    data["scripts"] = scripts
    package_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Added npm script '{script_name}' to package.json")


def _resolve_init_target_path(
    *,
    config_path: Path | None,
    use_global: bool,
    local_only: bool,
) -> Path:
    if config_path is not None:
        return config_path
    if use_global:
        return global_config_path()
    if local_only:
        return Path.cwd() / "pcf-proxy.yaml"
    return default_config_path()


def _run_init_flow(
    *,
    target_path: Path,
    project_root: Path,
    force: bool,
    interactive: bool,
    crm_url: str | None,
    install_mitmproxy: bool | None,
) -> Path:
    header_comment = _build_config_header_comment(project_root, target_path)
    resolved_crm_url = crm_url
    selected_envs: list[EnvironmentConfig] = []
    existing = target_path.exists()
    if existing and not force:
        if interactive and _is_interactive():
            if typer.confirm("Config exists. Update it instead of overwriting?", default=True):
                _update_existing_config(
                    target_path=target_path,
                    project_root=project_root,
                    crm_url=crm_url,
                    install_mitmproxy=install_mitmproxy,
                )
                return target_path
        typer.secho(f"Config file already exists: {target_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if interactive:
        component_candidates = _detect_component_names(project_root)
        selected_envs, default_env_url, pac_was_available = _prompt_for_environments()
        if default_env_url is not None:
            resolved_crm_url = default_env_url
        elif not pac_was_available:
            # Only ask for manual URL if PAC wasn't available
            resolved_crm_url = _prompt_for_crm_url()
        dist_path = _prompt_for_dist_path(
            default=ProxyConfig().bundle.dist_path,
            project_root=project_root,
            component_candidates=component_candidates,
        )
        if install_mitmproxy is None:
            install_mitmproxy = typer.confirm("Install mitmproxy now (recommended)?", default=True)
        if install_mitmproxy:
            _attempt_mitmproxy_install()
        mitm_path = _prompt_for_mitmproxy_path(current=None, install_mitmproxy=install_mitmproxy)
    else:
        if install_mitmproxy:
            _attempt_mitmproxy_install()
        dist_path = None
        mitm_path = None

    try:
        write_default_config(
            target_path,
            overwrite=force,
            header_comment=header_comment,
        )
    except FileExistsError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if resolved_crm_url:
        _patch_crm_url(target_path, resolved_crm_url)
    if dist_path:
        _patch_bundle_dist_path(target_path, dist_path)
    if mitm_path:
        _patch_mitmproxy_path(target_path, mitm_path)
    if selected_envs:
        _patch_environments(target_path, selected_envs)
    if target_path == global_config_path():
        resolved_project_root = _prompt_for_project_root(project_root) if interactive else project_root
        _patch_project_root(target_path, resolved_project_root)
        typer.echo(f"Global config saved at {target_path}. You can run the proxy from any directory.")
        typer.echo("Start anywhere with: pcf-toolkit proxy start --global <component>")
    return target_path


def _attempt_mitmproxy_install() -> None:
    try:
        ensure_mitmproxy(True, None)
        typer.secho("mitmproxy is ready.", fg=typer.colors.GREEN)
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"mitmproxy install failed: {exc}", fg=typer.colors.RED)


def _build_config_header_comment(project_root: Path, target_path: Path) -> list[str]:
    project_name = project_root.name
    repo_url = _git_remote_url(project_root)
    lines = [f"Project: {project_name}"]
    if repo_url:
        lines.append(f"Repo: {repo_url}")
    if target_path == global_config_path():
        lines.append("Global config: used when no local config is found.")
    lines.append("Install: uv tool install pcf-toolkit@latest")
    lines.append("Run without install: uvx pcf-toolkit")
    return lines


def _git_remote_url(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def _pac_available() -> bool:
    return shutil.which("pac") is not None


def _pac_auth_list() -> list[tuple[str, str, bool]]:
    try:
        result = subprocess.run(
            ["pac", "auth", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []
    return _parse_pac_auth_list(result.stdout)


def _parse_pac_auth_list(output: str) -> list[tuple[str, str, bool]]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    header_index = None
    header_line = ""
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("Index") and "Environment Url" in line:
            header_index = idx
            header_line = line
            break
    if header_index is None:
        return []

    env_col_start = header_line.find("Environment")
    url_col_start = header_line.find("Environment Url")
    if env_col_start < 0:
        env_col_start = None
    if url_col_start < 0:
        url_col_start = None

    entries: list[tuple[str, str, bool]] = []
    for line in lines[header_index + 1 :]:
        if not line.strip().startswith("["):
            continue
        url_match = re.search(r"https?://\S+", line)
        if not url_match:
            continue
        url = url_match.group(0)
        active = "*" in line
        env_name = None
        if env_col_start is not None:
            end = url_match.start()
            if url_col_start is not None and url_col_start > env_col_start:
                end = min(end, url_col_start)
            if end > env_col_start:
                env_name = line[env_col_start:end].strip() or None
        if not env_name:
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 2:
                env_name = parts[-2].strip()
        if not env_name:
            env_name = url
        entries.append((env_name, url, active))
    return entries


def _prompt_for_environments() -> tuple[list[EnvironmentConfig], str | None, bool]:
    """Prompt user to select environments from PAC auth.

    Returns:
        Tuple of (selected environments, default URL, pac_available flag).
        The pac_available flag indicates if PAC was available - if True,
        the caller should NOT prompt for a manual URL since we've already
        handled environment selection from PAC.
    """
    if not _pac_available():
        typer.secho(
            "PAC CLI not detected. Install it to auto-select environments.",
            fg=typer.colors.YELLOW,
        )
        return [], None, False

    entries = _pac_auth_list()
    if not entries:
        typer.secho("No PAC auth environments found.", fg=typer.colors.YELLOW)
        return [], None, False

    selected_entries = _prompt_select_pac_environments(entries)
    if not selected_entries:
        # User had environments available but chose not to select any.
        # Use the active environment as default instead of asking again.
        active_entry = next((e for e in entries if e[2]), entries[0])
        typer.secho(
            f"Using active environment: {active_entry[0]} ({active_entry[1]})",
            fg=typer.colors.CYAN,
        )
        return [], active_entry[1], True

    envs = [EnvironmentConfig(name=name, url=url, active=active) for name, url, active in selected_entries]
    default_env = _pick_active_environment(envs)
    if default_env:
        typer.secho(
            f"Default environment: {default_env.name} ({default_env.url})",
            fg=typer.colors.CYAN,
        )
    return envs, default_env.url if default_env else None, True


def _prompt_for_crm_url() -> str | None:
    return typer.prompt("Dynamics environment URL", default="", show_default=False) or None


def _prompt_select_pac_environments(entries: list[tuple[str, str, bool]]) -> list[tuple[str, str, bool]]:
    if not entries:
        return []
    choices = [_format_env_choice(idx, name, url, active) for idx, (name, url, active) in enumerate(entries, start=1)]
    if questionary is not None and sys.stdout.isatty():
        # Find the active environment indicator for the prompt hint
        active_name = next((name for name, _, active in entries if active), entries[0][0])
        selected = questionary.checkbox(
            f"Select environment(s) to save (skip to use {active_name})",
            choices=choices,
        ).ask()
        if not selected:
            return []
        indices = [_parse_choice_index(item) for item in selected]
        return [entries[idx - 1] for idx in indices if 1 <= idx <= len(entries)]

    selected_entries: list[tuple[str, str, bool]] = []
    while True:
        picked_url = _prompt_select_environment(entries)
        if picked_url is None:
            break
        for entry in entries:
            if entry[1] == picked_url and entry not in selected_entries:
                selected_entries.append(entry)
                break
        if not typer.confirm("Work with another environment?", default=False):
            break
    return selected_entries


def _prompt_for_project_root(project_root: Path) -> Path:
    if not _is_interactive():
        return project_root
    entered = typer.prompt("Project root for this global config", default=str(project_root))
    return Path(entered).expanduser()


def _prompt_for_dist_path(
    *,
    default: str,
    project_root: Path,
    component_candidates: list[str],
) -> str | None:
    if not _is_interactive():
        return default
    candidates = _collect_dist_path_candidates(project_root, default)
    if component_candidates:
        sample = component_candidates[0]
        resolved = project_root / default.replace("{PCF_NAME}", sample)
        suffix = "exists" if resolved.exists() else "missing"
        typer.secho(
            f"Detected control name: {sample} (resolved {resolved} is {suffix})",
            fg=typer.colors.CYAN if resolved.exists() else typer.colors.YELLOW,
        )
    if questionary is not None and sys.stdout.isatty() and len(candidates) > 1:
        choices = list(candidates)
        custom_choice = "Enter a custom path"
        choices.append(custom_choice)
        picked = questionary.select(
            "Select a dist path template",
            choices=choices,
            default=default if default in choices else choices[0],
            use_shortcuts=True,
        ).ask()
        if picked == custom_choice:
            return typer.prompt("Dist path template", default=default)
        if picked:
            return str(picked)
    return typer.prompt("Dist path template", default=default)


def _collect_dist_path_candidates(project_root: Path, default: str) -> list[str]:
    candidates: list[str] = []
    for template in (default, "dist/controls/{PCF_NAME}", "dist/{PCF_NAME}"):
        if template not in candidates:
            candidates.append(template)
    for base in ("out/controls", "dist/controls", "dist", "build"):
        if (project_root / base).exists():
            template = f"{base}/{{PCF_NAME}}"
            if template not in candidates:
                candidates.append(template)
    return candidates


def _prompt_for_mitmproxy_path(
    *,
    current: Path | None,
    install_mitmproxy: bool | None,
) -> Path | None:
    if not _is_interactive():
        return current
    detected = find_mitmproxy(current)
    if detected is None:
        return current
    prompt = f"Store mitmproxy path in config ({detected})?"
    if typer.confirm(prompt, default=True):
        return detected
    return current


def _update_existing_config(
    *,
    target_path: Path,
    project_root: Path,
    crm_url: str | None,
    install_mitmproxy: bool | None,
) -> None:
    existing = load_config(target_path, cwd=project_root).config
    component_candidates = _detect_component_names(project_root)
    resolved_crm_url = crm_url
    selected_envs: list[EnvironmentConfig] = []
    pac_was_available = False
    if _pac_available() and _is_interactive():
        if typer.confirm("Update environment list from PAC auth?", default=True):
            selected_envs, default_env_url, pac_was_available = _prompt_for_environments()
            if default_env_url is not None:
                resolved_crm_url = default_env_url
    if resolved_crm_url is None and not pac_was_available:
        # Only ask for manual URL if we didn't get one from PAC
        resolved_crm_url = (
            typer.prompt(
                "Dynamics environment URL",
                default=existing.crm_url or "",
                show_default=bool(existing.crm_url),
            )
            or None
        )
    dist_path = _prompt_for_dist_path(
        default=existing.bundle.dist_path,
        project_root=project_root,
        component_candidates=component_candidates,
    )
    if install_mitmproxy is None:
        install_mitmproxy = typer.confirm("Install mitmproxy now (recommended)?", default=existing.auto_install)
    if install_mitmproxy:
        _attempt_mitmproxy_install()
    mitm_path = _prompt_for_mitmproxy_path(current=existing.mitmproxy.path, install_mitmproxy=install_mitmproxy)
    if resolved_crm_url:
        _patch_crm_url(target_path, resolved_crm_url)
    if dist_path:
        _patch_bundle_dist_path(target_path, dist_path)
    if mitm_path:
        _patch_mitmproxy_path(target_path, mitm_path)
    if selected_envs:
        _patch_environments(target_path, selected_envs)
    if target_path == global_config_path():
        resolved_project_root = _prompt_for_project_root(project_root)
        _patch_project_root(target_path, resolved_project_root)


def _patch_crm_url(path: Path, crm_url: str) -> None:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["crm_url"] = crm_url
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    updated = False
    for idx, line in enumerate(lines):
        if line.strip().startswith("crm_url:"):
            lines[idx] = f'crm_url: "{crm_url}"'
            updated = True
            break
    if not updated:
        lines.append(f'crm_url: "{crm_url}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _patch_project_root(path: Path, project_root: Path) -> None:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["project_root"] = str(project_root)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    updated = False
    for idx, line in enumerate(lines):
        if line.strip().startswith("project_root:"):
            lines[idx] = f'project_root: "{project_root}"'
            updated = True
            break
    if not updated:
        lines.append(f'project_root: "{project_root}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _patch_bundle_dist_path(path: Path, dist_path: str) -> None:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        bundle = data.get("bundle") or {}
        bundle["dist_path"] = dist_path
        data["bundle"] = bundle
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    _patch_yaml_nested_key(path, "bundle", "dist_path", dist_path)


def _patch_mitmproxy_path(path: Path, mitm_path: Path) -> None:
    value = str(mitm_path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        mitm = data.get("mitmproxy") or {}
        mitm["path"] = value
        data["mitmproxy"] = mitm
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    _patch_yaml_nested_key(path, "mitmproxy", "path", value)


def _patch_environments(path: Path, envs: list[EnvironmentConfig]) -> None:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["environments"] = [{"name": env.name, "url": env.url, "active": env.active} for env in envs]
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    block = _format_environments_yaml(envs)
    lines = _replace_yaml_block(lines, "environments", block)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_environments_yaml(envs: list[EnvironmentConfig]) -> list[str]:
    lines = ["environments:"]
    for env in envs:
        lines.append(f"  - name: {_yaml_format_value(env.name)}")
        lines.append(f"    url: {_yaml_format_value(env.url)}")
        if env.active:
            lines.append("    active: true")
    return lines


def _replace_yaml_block(lines: list[str], key: str, block: list[str]) -> list[str]:
    start = None
    end = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and stripped.startswith(f"{key}:"):
            start = idx
            continue
        if start is not None and indent == 0 and idx != start:
            end = idx
            break
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        return lines + block
    if end is None:
        end = len(lines)
    return lines[:start] + block + lines[end:]


def _patch_yaml_nested_key(path: Path, section: str, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    formatted = _yaml_format_value(value)
    section_index = None
    section_indent = 0
    updated = False
    insert_at = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if stripped.startswith(f"{section}:"):
            section_index = idx
            section_indent = indent
            insert_at = idx + 1
            continue
        if section_index is not None:
            if indent <= section_indent and stripped.endswith(":"):
                insert_at = idx
                break
            if stripped.startswith(f"{key}:"):
                lines[idx] = " " * (section_indent + 2) + f"{key}: {formatted}"
                updated = True
                break
            insert_at = idx + 1

    if not updated:
        if section_index is None:
            lines.append(f"{section}:")
            lines.append(" " * 2 + f"{key}: {formatted}")
        else:
            if insert_at is None:
                insert_at = section_index + 1
            lines.insert(insert_at, " " * (section_indent + 2) + f"{key}: {formatted}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _yaml_format_value(value: str) -> str:
    if value == "":
        return '""'
    if re.search(r"[:#\\s]", value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _handle_missing_config(project_root: Path, config_path: Path | None) -> None:
    if config_path is not None:
        _rich_tip(
            "Config not found",
            [
                "Pass a valid config via --config.",
                "Or run: pcf-toolkit proxy init",
            ],
        )
        return
    if not sys.stdout.isatty():
        _rich_tip(
            "Config not found",
            [
                "Run: pcf-toolkit proxy init",
                "Tip: use --global to run from anywhere.",
            ],
        )
        return
    _rich_tip(
        "Config not found",
        [
            "No proxy config found in this directory or global config.",
            "Create one now to continue.",
        ],
    )
    if typer.confirm("Create one now?", default=True):
        target = _resolve_init_target_path(
            config_path=None,
            use_global=typer.confirm("Store globally (so you can run anywhere)?", default=False),
            local_only=False,
        )
        _run_init_flow(
            target_path=target,
            project_root=project_root,
            force=False,
            interactive=True,
            crm_url=None,
            install_mitmproxy=None,
        )
        typer.echo("Config created. Re-run your command.")


def _resolve_environment(config: ProxyConfig, requested: str | None) -> tuple[ProxyConfig, EnvironmentConfig | None]:
    envs = config.environments or []
    if not envs:
        return config, None

    selected: EnvironmentConfig | None = None
    if requested:
        selected = _match_environment(envs, requested)
        if selected is None:
            available = ", ".join(env.name for env in envs) or "none"
            _rich_tip(
                "Environment not found",
                [
                    f"Requested: {requested}",
                    f"Available: {available}",
                    "Run: pcf-toolkit proxy start --env <name>",
                ],
            )
            raise typer.Exit(code=1)
    elif _is_interactive() and len(envs) > 1:
        selected = _prompt_select_config_environment(envs)
    if selected is None:
        selected = _pick_active_environment(envs) or envs[0]

    if selected.url:
        config = config.model_copy(update={"crm_url": selected.url})
    return config, selected


def _match_environment(envs: list[EnvironmentConfig], requested: str) -> EnvironmentConfig | None:
    cleaned = requested.strip()
    if cleaned.isdigit():
        index = int(cleaned)
        if 1 <= index <= len(envs):
            return envs[index - 1]
    for env in envs:
        if env.name.lower() == cleaned.lower():
            return env
    for env in envs:
        if env.url.lower() == cleaned.lower():
            return env
    return None


def _pick_active_environment(
    envs: list[EnvironmentConfig],
) -> EnvironmentConfig | None:
    for env in envs:
        if env.active:
            return env
    return envs[0] if envs else None


def _prompt_select_config_environment(
    envs: list[EnvironmentConfig],
) -> EnvironmentConfig | None:
    if not envs:
        return None
    choices = [_format_env_choice(idx, env.name, env.url, env.active) for idx, env in enumerate(envs, start=1)]
    default_env = _pick_active_environment(envs) or envs[0]
    default_index = envs.index(default_env) + 1
    if questionary is not None and sys.stdout.isatty():
        choice = questionary.select(
            "Select a Dynamics environment",
            choices=choices,
            default=choices[default_index - 1],
            use_shortcuts=True,
        ).ask()
        if not choice:
            return None
        selected_index = _parse_choice_index(choice)
        if 1 <= selected_index <= len(envs):
            return envs[selected_index - 1]
        return None

    typer.echo("Select a Dynamics environment:")
    for item in choices:
        typer.echo(f"  {item}")
    pick = typer.prompt("Pick an environment", default=default_index, type=int)
    pick = max(1, min(pick, len(envs)))
    return envs[pick - 1]


def _format_env_choice(index: int, name: str, url: str, active: bool) -> str:
    marker = "★" if active else " "
    return f"[{index}] {marker} {name} - {url}"


def _parse_choice_index(choice: str) -> int:
    try:
        return int(choice.split("]")[0].lstrip("["))
    except Exception:
        return 0


def _prompt_select_environment(entries: list[tuple[str, str, bool]]) -> str | None:
    if not entries:
        return typer.prompt("Dynamics environment URL", default="", show_default=False) or None
    default_index = next((i for i, item in enumerate(entries, start=1) if item[2]), 1)
    choices = [_format_env_choice(idx, name, url, active) for idx, (name, url, active) in enumerate(entries, start=1)]

    if questionary is not None and sys.stdout.isatty():
        choice = questionary.select(
            "Select a Dynamics environment",
            choices=choices,
            default=choices[default_index - 1],
            use_shortcuts=True,
        ).ask()
        if not choice:
            return None
        selected_index = _parse_choice_index(choice)
        return entries[selected_index - 1][1]

    typer.echo("Select a Dynamics environment:")
    for item in choices:
        typer.echo(f"  {item}")
    pick = typer.prompt("Pick an environment", default=default_index, type=int)
    pick = max(1, min(pick, len(entries)))
    return entries[pick - 1][1]


def _rich_tip(title: str, lines: list[str]) -> None:
    console = rich_console(stderr=True)
    if console is None or Panel is None or Text is None or Table is None:
        typer.echo(f"{title}: " + " ".join(lines), err=True)
        return
    sections = _split_tip_lines(lines)
    body = _build_tip_table(sections)
    panel = Panel(body, title=title, title_align="left", border_style="cyan")
    console.print(panel)


def _resolve_component_name(project_root: Path, config: ProxyConfig | None = None) -> str:
    candidates = _detect_component_names(project_root)
    if not candidates:
        _rich_tip(
            "Component not found",
            [
                "No ControlManifest.Input.xml or manifest.yaml/json found.",
                "Run: pcf-toolkit proxy start <ComponentName>",
            ],
        )
        raise typer.Exit(code=1)
    if config is not None:
        existing = [name for name in candidates if render_dist_path(config, name, project_root).exists()]
        if existing:
            candidates = existing
    if len(candidates) == 1 or not _is_interactive():
        return candidates[0]
    choice = _prompt_select_component(candidates)
    return choice or candidates[0]


def _prompt_select_component(candidates: list[str]) -> str | None:
    if not candidates:
        return None
    if questionary is not None and sys.stdout.isatty():
        return questionary.select(
            "Select a component",
            choices=candidates,
            default=candidates[0],
            use_shortcuts=True,
        ).ask()
    typer.echo("Select a component:")
    for idx, name in enumerate(candidates, start=1):
        typer.echo(f"  [{idx}] {name}")
    pick = typer.prompt("Pick a component", default=1, type=int)
    pick = max(1, min(pick, len(candidates)))
    return candidates[pick - 1]


def _detect_component_names(project_root: Path) -> list[str]:
    candidates: list[str] = []
    for path in project_root.rglob("ControlManifest.Input.xml"):
        if not path.is_file():
            continue
        parsed = _parse_manifest_xml(path)
        for name in parsed:
            if name not in candidates:
                candidates.append(name)
        if len(candidates) >= 5:
            break
    for name in _parse_manifest_yaml_json(project_root):
        if name not in candidates:
            candidates.append(name)
    return candidates


def _parse_manifest_xml(path: Path) -> list[str]:
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(path)
        root = tree.getroot()

        def _strip_ns(tag: str) -> str:
            if "}" in tag:
                return tag.split("}", 1)[1]
            return tag

        if _strip_ns(root.tag) == "control":
            control = root
        else:
            control = next(
                (child for child in root if _strip_ns(child.tag) == "control"),
                None,
            )
        if control is None:
            return []
        namespace = control.attrib.get("namespace")
        constructor = control.attrib.get("constructor")
        if not constructor:
            return []
        names = [constructor]
        if namespace:
            names.insert(0, f"{namespace}.{constructor}")
        return names
    except Exception:  # noqa: BLE001
        return []


def _parse_manifest_yaml_json(project_root: Path) -> list[str]:
    candidates: list[str] = []
    for filename in ("manifest.yaml", "manifest.yml", "manifest.json"):
        path = project_root / filename
        if not path.exists():
            continue
        try:
            if path.suffix.lower() == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        control = data.get("control", {}) if isinstance(data, dict) else {}
        namespace = control.get("namespace")
        constructor = control.get("constructor")
        if constructor:
            candidates.append(constructor)
            if namespace:
                candidates.append(f"{namespace}.{constructor}")
    return candidates


def _split_tip_lines(lines: list[str]) -> dict[str, list[str]]:
    sections = {"info": [], "expected": [], "actions": [], "tips": []}
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("expected:"):
            sections["expected"].append(line.split(":", 1)[1].strip())
            continue
        if lower.startswith("tip:"):
            sections["tips"].append(line.split(":", 1)[1].strip())
            continue
        action_match = re.search(r"\brun:\s*(.+)$", line, re.IGNORECASE)
        if action_match:
            prefix = line[: action_match.start()].strip(" :")
            command = action_match.group(1).strip()
            if prefix and prefix.lower() not in ("or", "run"):
                sections["info"].append(prefix)
            if command:
                sections["actions"].append(command)
            continue
        sections["info"].append(line)
    return sections


def _build_tip_table(sections: dict[str, list[str]]) -> Table:
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold", no_wrap=True)
    table.add_column()
    info = sections.get("info", [])
    for idx, line in enumerate(info):
        label = "Info" if idx == 0 else ""
        table.add_row(label, Text(line))
    for line in sections.get("expected", []):
        table.add_row("Expected", Text(line))
    for line in sections.get("actions", []):
        table.add_row("Try", _style_command(line))
    for line in sections.get("tips", []):
        table.add_row("Tip", Text(line))
    return table


def _style_command(command: str) -> Text:
    text = Text(command)
    if command:
        text.stylize("bold cyan")
    return text


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _session_dir(project_root: Path) -> Path:
    return project_root / ".pcf-toolkit"


def _write_session(session_dir: Path, session: ProxySession) -> None:
    session_path = session_dir / "proxy.session.json"
    session_path.write_text(json.dumps(asdict(session), indent=2) + "\n", encoding="utf-8")


def _read_session(session_path: Path) -> ProxySession:
    data = json.loads(session_path.read_text(encoding="utf-8"))
    return ProxySession(**data)


def _clear_session(session_dir: Path) -> None:
    session_path = session_dir / "proxy.session.json"
    if session_path.exists():
        session_path.unlink()


def _terminate_proc(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            return


def _terminate_pid(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
