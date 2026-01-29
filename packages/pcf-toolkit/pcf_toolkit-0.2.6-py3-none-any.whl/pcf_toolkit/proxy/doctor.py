"""Doctor checks for the proxy workflow."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from pcf_toolkit.proxy.browser import find_browser_binary
from pcf_toolkit.proxy.config import ProxyConfig, render_dist_path
from pcf_toolkit.proxy.mitm import find_mitmproxy


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str
    fix: str | None = None


def run_doctor(
    config: ProxyConfig | None,
    config_path: Path | None,
    component: str | None,
    project_root: Path,
) -> list[CheckResult]:
    """Runs diagnostic checks for proxy workflow prerequisites.

    Args:
      config: Proxy configuration (optional).
      config_path: Path to config file (optional).
      component: Component name to validate (optional).
      project_root: Project root directory.

    Returns:
      List of CheckResult objects describing check outcomes.
    """
    results: list[CheckResult] = []

    if config_path and not config_path.exists():
        results.append(
            CheckResult(
                name="config",
                status="fail",
                message=f"Config not found at {config_path}",
                fix="Run 'pcf-toolkit proxy init' to create one.",
            )
        )
    elif config_path:
        results.append(
            CheckResult(
                name="config",
                status="ok",
                message=f"Loaded config from {config_path}",
            )
        )

    if config:
        if not config.crm_url or "yourorg" in config.crm_url:
            results.append(
                CheckResult(
                    name="crm_url",
                    status="warn",
                    message="CRM URL is missing or still a placeholder.",
                    fix="Set 'crm_url' in your proxy config.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="crm_url",
                    status="ok",
                    message="CRM URL configured.",
                )
            )

        results.extend(_check_ports(config))
        results.extend(_check_mitmproxy(config))
        results.extend(_check_certificates())
        results.extend(_check_browser(config))

        if component:
            results.extend(_check_dist_path(config, component, project_root))
    else:
        results.append(
            CheckResult(
                name="config",
                status="fail",
                message="Config was not loaded.",
                fix="Run 'pcf-toolkit proxy init' and set required values.",
            )
        )

    return results


def check_mitmproxy_certificate() -> CheckResult:
    """Returns a single check result for mitmproxy certificate trust."""
    return _check_certificates()[0]


def _check_ports(config: ProxyConfig) -> list[CheckResult]:
    """Checks if proxy and HTTP server ports are available.

    Args:
      config: Proxy configuration.

    Returns:
      List of CheckResult objects for port availability.
    """
    results = []
    for label, host, port in (
        ("proxy_port", config.proxy.host, config.proxy.port),
        ("http_port", config.http_server.host, config.http_server.port),
    ):
        if _port_available(host, port):
            results.append(
                CheckResult(
                    name=label,
                    status="ok",
                    message=f"{host}:{port} is available.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=label,
                    status="fail",
                    message=f"{host}:{port} is already in use.",
                    fix="Change the port in config or stop the process using it.",
                )
            )
    return results


def _check_mitmproxy(config: ProxyConfig) -> list[CheckResult]:
    """Checks if mitmproxy is available.

    Args:
      config: Proxy configuration.

    Returns:
      List of CheckResult objects for mitmproxy availability.
    """
    binary = find_mitmproxy(config.mitmproxy.path)
    if binary:
        return [
            CheckResult(
                name="mitmproxy",
                status="ok",
                message=f"mitmproxy available at {binary}",
            )
        ]
    return [
        CheckResult(
            name="mitmproxy",
            status="fail",
            message="mitmproxy not found.",
            fix="Install mitmproxy or run 'pcf-toolkit proxy doctor --fix'.",
        )
    ]


def _check_certificates() -> list[CheckResult]:
    """Checks if mitmproxy CA certificate is installed.

    Returns:
      List of CheckResult objects for certificate status.
    """
    cert_dir = Path.home() / ".mitmproxy"
    cert_file = cert_dir / "mitmproxy-ca-cert.pem"
    if cert_file.exists():
        trusted = _is_cert_trusted(cert_file)
        if trusted is True:
            return [
                CheckResult(
                    name="mitmproxy_cert",
                    status="ok",
                    message="mitmproxy CA cert is trusted.",
                )
            ]
        if trusted is False:
            return [
                CheckResult(
                    name="mitmproxy_cert",
                    status="warn",
                    message="mitmproxy CA cert exists but is not trusted.",
                    fix=_cert_fix_instructions(cert_dir),
                )
            ]
        return [
            CheckResult(
                name="mitmproxy_cert",
                status="warn",
                message="mitmproxy CA cert found but trust status is unknown.",
                fix=_cert_fix_instructions(cert_dir),
            )
        ]
    return [
        CheckResult(
            name="mitmproxy_cert",
            status="warn",
            message="mitmproxy CA cert not found.",
            fix=_cert_fix_instructions(cert_dir),
        )
    ]


def _check_browser(config: ProxyConfig) -> list[CheckResult]:
    """Checks if browser is available.

    Args:
      config: Proxy configuration.

    Returns:
      List of CheckResult objects for browser availability.
    """
    binary = find_browser_binary(config.browser.prefer, config.browser.path)
    if binary:
        return [
            CheckResult(
                name="browser",
                status="ok",
                message=f"Browser found at {binary}",
            )
        ]
    return [
        CheckResult(
            name="browser",
            status="warn",
            message="Browser not found.",
            fix="Set 'browser.path' in config or install Chrome/Edge.",
        )
    ]


def _check_dist_path(config: ProxyConfig, component: str, project_root: Path) -> list[CheckResult]:
    """Checks if component dist path exists.

    Args:
      config: Proxy configuration.
      component: Component name.
      project_root: Project root directory.

    Returns:
      List of CheckResult objects for dist path status.
    """
    dist_path = render_dist_path(config, component, project_root)
    if dist_path.exists():
        return [
            CheckResult(
                name="dist_path",
                status="ok",
                message=f"Dist path exists at {dist_path}",
            )
        ]
    return [
        CheckResult(
            name="dist_path",
            status="warn",
            message=f"Dist path missing: {dist_path}",
            fix="Run 'npm run build' or adjust 'bundle.dist_path' in config.",
        )
    ]


def _port_available(host: str, port: int) -> bool:
    """Checks if a port is available for binding.

    Args:
      host: Hostname to bind to.
      port: Port number to check.

    Returns:
      True if port is available, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _cert_fix_instructions(cert_dir: Path) -> str:
    """Generates platform-specific certificate installation instructions.

    Args:
      cert_dir: Directory containing mitmproxy certificate.

    Returns:
      Command string for installing the certificate.
    """
    cert_path = cert_dir / "mitmproxy-ca-cert.pem"
    if os.name == "nt":
        return f"Run: certutil -addstore -f Root {cert_path} (elevated)"
    if sys.platform == "darwin":
        return (
            "Run: sudo security add-trusted-cert -d -r trustRoot "
            f"-k /Library/Keychains/System.keychain {cert_path}"
        )
    if shutil.which("update-ca-certificates"):
        return (
            f"Run: sudo cp {cert_path} /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt "
            "&& sudo update-ca-certificates"
        )
    if shutil.which("update-ca-trust"):
        return (
            f"Run: sudo cp {cert_path} /etc/pki/ca-trust/source/anchors/mitmproxy-ca-cert.pem "
            "&& sudo update-ca-trust extract"
        )
    return f"Trust the cert manually: {cert_path}"


def _is_cert_trusted(cert_path: Path) -> bool | None:
    """Best-effort check for whether the mitmproxy CA is trusted."""
    if sys.platform == "darwin":
        return _is_cert_trusted_macos(cert_path)
    if sys.platform.startswith("linux"):
        return _is_cert_trusted_linux(cert_path)
    if os.name == "nt":
        return _is_cert_trusted_windows(cert_path)
    return None


def _is_cert_trusted_macos(cert_path: Path) -> bool | None:
    try:
        result = subprocess.run(
            [
                "security",
                "find-certificate",
                "-c",
                "mitmproxy",
                "-a",
                "/Library/Keychains/System.keychain",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def _is_cert_trusted_linux(cert_path: Path) -> bool:
    candidates = [
        Path("/usr/local/share/ca-certificates/mitmproxy-ca-cert.crt"),
        Path("/etc/ssl/certs/mitmproxy-ca-cert.pem"),
        Path("/etc/ssl/certs/mitmproxy-ca-cert.crt"),
        Path("/etc/pki/ca-trust/source/anchors/mitmproxy-ca-cert.pem"),
        Path("/etc/pki/ca-trust/source/anchors/mitmproxy-ca-cert.crt"),
    ]
    return any(path.exists() for path in candidates)


def _is_cert_trusted_windows(cert_path: Path) -> bool | None:
    # Implementing a reliable trust-store check on Windows is non-trivial here.
    # Fall back to unknown and let the CLI provide instructions.
    return None
