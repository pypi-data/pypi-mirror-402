"""Shared CLI utilities for rich output."""

from __future__ import annotations

from collections.abc import Iterable

try:
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover - fallback if rich isn't available
    Console = None
    Table = None


def rich_console(stderr: bool = False):
    """Returns a Rich console if available, otherwise None.

    Args:
      stderr: If True, creates a console that writes to stderr.

    Returns:
      A Rich Console instance if Rich is available, otherwise None.
    """
    if Console is None:
        return None
    return Console(stderr=stderr)


def render_validation_table(
    errors: Iterable[dict],
    *,
    title: str,
    stderr: bool = True,
) -> bool:
    """Renders a validation error table using Rich.

    Args:
      errors: Iterable of validation error dictionaries.
      title: Title for the error table.
      stderr: If True, writes to stderr instead of stdout.

    Returns:
      True if the table was rendered successfully, False otherwise.
    """
    if Table is None:
        return False

    console = rich_console(stderr=stderr)
    if console is None:
        return False

    table = Table(title=title, show_lines=False)
    table.add_column("Location", style="bold")
    table.add_column("Message")
    table.add_column("Type", style="dim")
    for error in errors:
        loc = ".".join(str(part) for part in error.get("loc", [])) or "<root>"
        msg = error.get("msg", "Invalid value")
        err_type = error.get("type", "validation_error")
        table.add_row(loc, msg, err_type)
    console.print(table)
    return True
