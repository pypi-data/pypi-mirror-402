"""Mitmproxy bootstrap helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MitmproxyInstall:
    binary: Path
    venv_dir: Path


def managed_venv_dir() -> Path:
    """Returns the path to the managed mitmproxy virtual environment.

    Returns:
      Path to ~/.pcf-toolkit/venvs/mitmproxy.
    """
    return Path.home() / ".pcf-toolkit" / "venvs" / "mitmproxy"


def find_mitmproxy(explicit_path: Path | None = None) -> Path | None:
    """Finds mitmproxy executable.

    Searches system PATH and managed venv.

    Args:
      explicit_path: Explicit path to mitmproxy binary.

    Returns:
      Path to mitmproxy executable, or None if not found.
    """
    if explicit_path and explicit_path.exists():
        return explicit_path

    for candidate in ("mitmdump", "mitmproxy"):
        resolved = shutil.which(candidate)
        if resolved:
            return Path(resolved)

    venv_dir = managed_venv_dir()
    for candidate in ("mitmdump", "mitmproxy"):
        resolved = _venv_bin_path(venv_dir, candidate)
        if resolved and resolved.exists():
            return resolved

    return None


def ensure_mitmproxy(auto_install: bool, explicit_path: Path | None = None) -> Path:
    """Ensures mitmproxy is available, installing if needed.

    Args:
      auto_install: If True, installs mitmproxy if not found.
      explicit_path: Explicit path to mitmproxy binary.

    Returns:
      Path to mitmproxy executable.

    Raises:
      FileNotFoundError: If mitmproxy not found and auto_install is False.
    """
    existing = find_mitmproxy(explicit_path)
    if existing:
        return existing
    if not auto_install:
        raise FileNotFoundError("mitmproxy not found")
    install = install_mitmproxy(managed_venv_dir())
    return install.binary


def install_mitmproxy(venv_dir: Path) -> MitmproxyInstall:
    """Installs mitmproxy into a virtual environment.

    Args:
      venv_dir: Directory for the virtual environment.

    Returns:
      MitmproxyInstall instance with binary and venv paths.

    Raises:
      FileNotFoundError: If installation fails to produce a binary.
    """
    venv_dir.mkdir(parents=True, exist_ok=True)
    python_bin = _venv_python(venv_dir)
    if not python_bin.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python_bin = _venv_python(venv_dir)
    _ensure_pip(python_bin)
    subprocess.run(
        [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ],
        check=True,
    )
    subprocess.run([str(python_bin), "-m", "pip", "install", "mitmproxy"], check=True)
    mitm_binary = _venv_bin_path(venv_dir, "mitmdump")
    if mitm_binary is None or not mitm_binary.exists():
        mitm_binary = _venv_bin_path(venv_dir, "mitmproxy")
    if mitm_binary is None:
        raise FileNotFoundError("mitmproxy install did not produce a binary")
    return MitmproxyInstall(binary=mitm_binary, venv_dir=venv_dir)


def spawn_mitmproxy(
    binary: Path,
    addon_path: Path,
    host: str,
    port: int,
    env: dict[str, str],
    stdout=None,
    stderr=None,
    start_new_session: bool = False,
    creationflags: int = 0,
) -> subprocess.Popen:
    """Spawns a mitmproxy process with the redirect addon.

    Args:
      binary: Path to mitmproxy executable.
      addon_path: Path to the redirect addon script.
      host: Hostname to listen on.
      port: Port to listen on.
      env: Environment variables to pass to the process.
      stdout: Standard output handle (optional).
      stderr: Standard error handle (optional).
      start_new_session: If True, starts process in new session.
      creationflags: Windows process creation flags.

    Returns:
      Popen instance for the mitmproxy process.
    """
    cmd = [
        str(binary),
        "-s",
        str(addon_path),
        "--listen-host",
        host,
        "--listen-port",
        str(port),
    ]
    return subprocess.Popen(
        cmd,
        env=env,
        stdout=stdout,
        stderr=stderr,
        start_new_session=start_new_session,
        creationflags=creationflags,
    )


def _ensure_pip(python_bin: Path) -> None:
    """Ensures pip is available in the Python installation.

    Args:
      python_bin: Path to Python executable.
    """
    try:
        subprocess.run(
            [str(python_bin), "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        subprocess.run([str(python_bin), "-m", "ensurepip"], check=True)


def _venv_python(venv_dir: Path) -> Path:
    """Returns the path to Python executable in a virtual environment.

    Args:
      venv_dir: Virtual environment directory.

    Returns:
      Path to Python executable.
    """
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_bin_path(venv_dir: Path, name: str) -> Path | None:
    """Returns the path to an executable in a virtual environment.

    Args:
      venv_dir: Virtual environment directory.
      name: Executable name.

    Returns:
      Path to executable, or None if venv structure is invalid.
    """
    bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    if os.name == "nt":
        return bin_dir / f"{name}.exe"
    return bin_dir / name
