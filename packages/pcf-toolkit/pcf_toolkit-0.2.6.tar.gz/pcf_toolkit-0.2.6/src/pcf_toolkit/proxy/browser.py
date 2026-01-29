"""Browser discovery and launch helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_browser_binary(browser: str | None, explicit_path: Path | None) -> Path | None:
    """Finds a browser executable binary.

    Args:
      browser: Browser preference ("chrome", "edge", or None for auto).
      explicit_path: Explicit path to browser binary.

    Returns:
      Path to browser executable, or None if not found.
    """
    if explicit_path and explicit_path.exists():
        return explicit_path

    if browser:
        normalized = browser.lower()
    else:
        normalized = "auto"

    if normalized in {"chrome", "google-chrome"}:
        return _find_chrome()
    if normalized in {"edge", "microsoft-edge"}:
        return _find_edge()
    if normalized in {"auto", ""}:
        return _find_chrome() or _find_edge()

    resolved = shutil.which(browser)
    if resolved:
        return Path(resolved)

    return None


def launch_browser(
    binary: Path,
    crm_url: str,
    proxy_host: str,
    proxy_port: int,
    profile_dir: Path,
) -> subprocess.Popen:
    """Launches a browser with proxy configuration.

    Args:
      binary: Path to browser executable.
      crm_url: CRM URL to open.
      proxy_host: Proxy server hostname.
      proxy_port: Proxy server port.
      profile_dir: Directory for browser profile data.

    Returns:
      Popen instance for the browser process.
    """
    profile_dir.mkdir(parents=True, exist_ok=True)
    args = [
        str(binary),
        f"--proxy-server={proxy_host}:{proxy_port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        crm_url,
    ]
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=os.name != "nt",
        creationflags=creationflags,
    )


def _find_chrome() -> Path | None:
    """Finds Google Chrome executable.

    Returns:
      Path to Chrome executable, or None if not found.
    """
    candidates = []
    if os.name == "nt":
        program_files = os.environ.get("PROGRAMFILES")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
        local_appdata = os.environ.get("LOCALAPPDATA")
        for base in (program_files, program_files_x86, local_appdata):
            if base:
                candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
        )
    else:
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            resolved = shutil.which(name)
            if resolved:
                return Path(resolved)

    return _first_existing(candidates)


def _find_edge() -> Path | None:
    """Finds Microsoft Edge executable.

    Returns:
      Path to Edge executable, or None if not found.
    """
    candidates = []
    if os.name == "nt":
        program_files = os.environ.get("PROGRAMFILES")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
        local_appdata = os.environ.get("LOCALAPPDATA")
        for base in (program_files, program_files_x86, local_appdata):
            if base:
                candidates.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                Path.home() / "Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            ]
        )
    else:
        for name in ("microsoft-edge", "microsoft-edge-stable"):
            resolved = shutil.which(name)
            if resolved:
                return Path(resolved)

    return _first_existing(candidates)


def _first_existing(paths: list[Path]) -> Path | None:
    """Returns the first path that exists.

    Args:
      paths: List of paths to check.

    Returns:
      First existing path, or None if none exist.
    """
    for path in paths:
        if path.exists():
            return path
    return None
