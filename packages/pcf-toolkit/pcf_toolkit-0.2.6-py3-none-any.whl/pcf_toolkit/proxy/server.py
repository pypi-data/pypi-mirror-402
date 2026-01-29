"""Local file server helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def spawn_http_server(
    directory: Path,
    host: str,
    port: int,
    stdout=None,
    stderr=None,
    start_new_session: bool = False,
    creationflags: int = 0,
) -> subprocess.Popen:
    """Spawns a local HTTP server process.

    Uses Python's built-in http.server module.

    Args:
      directory: Directory to serve files from.
      host: Hostname to bind to.
      port: Port to listen on.
      stdout: Standard output handle (optional).
      stderr: Standard error handle (optional).
      start_new_session: If True, starts process in new session.
      creationflags: Windows process creation flags.

    Returns:
      Popen instance for the HTTP server process.
    """
    cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(port),
        "--bind",
        host,
    ]
    return subprocess.Popen(
        cmd,
        cwd=directory,
        stdout=stdout,
        stderr=stderr,
        start_new_session=start_new_session,
        creationflags=creationflags,
    )
