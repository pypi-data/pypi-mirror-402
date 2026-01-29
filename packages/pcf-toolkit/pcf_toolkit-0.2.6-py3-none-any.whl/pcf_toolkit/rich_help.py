"""Custom Rich help formatting for the CLI."""

from __future__ import annotations

from collections import defaultdict

import click
import typer.core as core
import typer.rich_utils as rich_utils
from rich.align import Align
from rich.padding import Padding
from rich.panel import Panel


def rich_format_help_custom(
    *,
    obj: click.Command | click.Group,
    ctx: click.Context,
    markup_mode: rich_utils.MarkupModeStrict,
) -> None:
    """Prints Rich-formatted help with a custom examples panel.

    Args:
      obj: Click command or group to format help for.
      ctx: Click context.
      markup_mode: Rich markup mode for formatting.
    """
    console = rich_utils._get_rich_console()

    # Usage
    console.print(
        Padding(rich_utils.highlighter(obj.get_usage(ctx)), 1),
        style=rich_utils.STYLE_USAGE_COMMAND,
    )

    # Main help text
    if obj.help:
        console.print(
            Padding(
                Align(
                    rich_utils._get_help_text(
                        obj=obj,
                        markup_mode=markup_mode,
                    ),
                    pad=False,
                ),
                (0, 1, 1, 1),
            )
        )

    panel_to_arguments: defaultdict[str, list[click.Argument]] = defaultdict(list)
    panel_to_options: defaultdict[str, list[click.Option]] = defaultdict(list)

    for param in obj.get_params(ctx):
        if getattr(param, "hidden", False):
            continue
        if isinstance(param, click.Argument):
            panel_name = getattr(param, rich_utils._RICH_HELP_PANEL_NAME, None) or rich_utils.ARGUMENTS_PANEL_TITLE
            panel_to_arguments[panel_name].append(param)
        elif isinstance(param, click.Option):
            panel_name = getattr(param, rich_utils._RICH_HELP_PANEL_NAME, None) or rich_utils.OPTIONS_PANEL_TITLE
            panel_to_options[panel_name].append(param)

    default_arguments = panel_to_arguments.get(rich_utils.ARGUMENTS_PANEL_TITLE, [])
    rich_utils._print_options_panel(
        name=rich_utils.ARGUMENTS_PANEL_TITLE,
        params=default_arguments,
        ctx=ctx,
        markup_mode=markup_mode,
        console=console,
    )
    for panel_name, arguments in panel_to_arguments.items():
        if panel_name == rich_utils.ARGUMENTS_PANEL_TITLE:
            continue
        rich_utils._print_options_panel(
            name=panel_name,
            params=arguments,
            ctx=ctx,
            markup_mode=markup_mode,
            console=console,
        )

    default_options = panel_to_options.get(rich_utils.OPTIONS_PANEL_TITLE, [])
    rich_utils._print_options_panel(
        name=rich_utils.OPTIONS_PANEL_TITLE,
        params=default_options,
        ctx=ctx,
        markup_mode=markup_mode,
        console=console,
    )
    for panel_name, options in panel_to_options.items():
        if panel_name == rich_utils.OPTIONS_PANEL_TITLE:
            continue
        rich_utils._print_options_panel(
            name=panel_name,
            params=options,
            ctx=ctx,
            markup_mode=markup_mode,
            console=console,
        )

    if isinstance(obj, click.Group):
        panel_to_commands: defaultdict[str, list[click.Command]] = defaultdict(list)
        for command_name in obj.list_commands(ctx):
            command = obj.get_command(ctx, command_name)
            if command and not command.hidden:
                panel_name = getattr(command, rich_utils._RICH_HELP_PANEL_NAME, None) or rich_utils.COMMANDS_PANEL_TITLE
                panel_to_commands[panel_name].append(command)

        max_cmd_len = max(
            [len(command.name or "") for commands in panel_to_commands.values() for command in commands],
            default=0,
        )

        default_commands = panel_to_commands.get(rich_utils.COMMANDS_PANEL_TITLE, [])
        rich_utils._print_commands_panel(
            name=rich_utils.COMMANDS_PANEL_TITLE,
            commands=default_commands,
            markup_mode=markup_mode,
            console=console,
            cmd_len=max_cmd_len,
        )
        for panel_name, commands in panel_to_commands.items():
            if panel_name == rich_utils.COMMANDS_PANEL_TITLE:
                continue
            rich_utils._print_commands_panel(
                name=panel_name,
                commands=commands,
                markup_mode=markup_mode,
                console=console,
                cmd_len=max_cmd_len,
            )

    # Custom epilog panel (no line collapsing)
    if obj.epilog:
        title = "Examples & Tips" if isinstance(obj, click.Group) else "Examples"
        epilogue_text = rich_utils._make_rich_text(
            text=obj.epilog,
            markup_mode=markup_mode,
        )
        panel = Panel(
            epilogue_text,
            title=title,
            title_align="left",
            border_style="cyan",
        )
        console.print(Padding(panel, 1))


class RichTyperCommand(core.TyperCommand):
    """Typer command with custom Rich help output."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:  # type: ignore[override]
        if not core.HAS_RICH or self.rich_markup_mode is None:
            return super().format_help(ctx, formatter)
        return rich_format_help_custom(
            obj=self,
            ctx=ctx,
            markup_mode=self.rich_markup_mode,
        )


class RichTyperGroup(core.TyperGroup):
    """Typer group with custom Rich help output."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:  # type: ignore[override]
        if not core.HAS_RICH or self.rich_markup_mode is None:
            return super().format_help(ctx, formatter)
        return rich_format_help_custom(
            obj=self,
            ctx=ctx,
            markup_mode=self.rich_markup_mode,
        )
