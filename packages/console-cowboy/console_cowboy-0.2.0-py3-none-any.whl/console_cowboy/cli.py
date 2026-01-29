"""
Console Cowboy CLI - Portable Terminal Configuration Manager.

This CLI enables migration of terminal emulator configurations between
different terminal applications using the CTEC (Common Terminal Emulator
Configuration) format as an intermediate representation.

Commands:
    export: Export a terminal's configuration to CTEC format
    import: Import a CTEC configuration into a terminal's native format
    list: List supported terminal emulators
    convert: Convert directly between terminal configuration formats
"""

from pathlib import Path

import click

# Import to trigger registration
import console_cowboy.terminals  # noqa: F401
from console_cowboy.ctec import CTEC, CTECSerializer
from console_cowboy.ctec.serializers import OutputFormat
from console_cowboy.terminals import TerminalRegistry


def get_terminal_choices() -> list[str]:
    """Get list of available terminal names for CLI choices."""
    return TerminalRegistry.get_names()


def print_warnings(ctec: CTEC) -> None:
    """Print any warnings from the CTEC configuration."""
    if ctec.warnings:
        click.echo(click.style("\nWarnings:", fg="yellow", bold=True), err=True)
        for warning in ctec.warnings:
            click.echo(click.style(f"  - {warning}", fg="yellow"), err=True)


def print_terminal_specific(ctec: CTEC) -> None:
    """Print terminal-specific settings that couldn't be mapped."""
    if ctec.terminal_specific:
        click.echo(
            click.style(
                "\nTerminal-specific settings (not portable):", fg="cyan", bold=True
            ),
            err=True,
        )
        for setting in ctec.terminal_specific:
            click.echo(
                click.style(
                    f"  [{setting.terminal}] {setting.key} = {setting.value}", fg="cyan"
                ),
                err=True,
            )


@click.group()
@click.version_option()
def cli():
    """
    Console Cowboy - Hop terminals like you hop Linux distributions.

    A tool for making terminal configurations portable across different
    terminal emulators. Export your settings from one terminal and import
    them into another.

    CTEC uses YAML as its primary format, aligned with the iTerm2-Color-Schemes
    ecosystem for maximum compatibility with existing themes.

    Supported terminals: iTerm2, Ghostty, Alacritty, Kitty, Wezterm

    \b
    Examples:
        # Export iTerm2 config to CTEC format
        console-cowboy export iterm2 -o my-config.yaml

        # Import CTEC config into Ghostty format
        console-cowboy import my-config.yaml -t ghostty -o ~/.config/ghostty/config

        # Convert directly between terminals
        console-cowboy convert ~/.config/kitty/kitty.conf -f kitty -t alacritty

        # Generate JSON schema for editor validation
        console-cowboy schema -o ctec.schema.json
    """
    pass


@cli.command(name="list")
def list_terminals():
    """
    List all supported terminal emulators.

    Shows terminal names that can be used with the export, import, and
    convert commands.
    """
    click.echo(click.style("Supported terminal emulators:", bold=True))
    click.echo()
    for adapter in TerminalRegistry.list_terminals():
        click.echo(click.style(f"  {adapter.name}", fg="green", bold=True))
        click.echo(f"    {adapter.display_name}: {adapter.description}")
        if adapter.default_config_paths:
            paths = ", ".join(f"~/{p}" for p in adapter.default_config_paths)
            click.echo(click.style(f"    Config: {paths}", dim=True))
        click.echo()


@cli.command(name="export")
@click.argument(
    "terminal",
    type=click.Choice(get_terminal_choices(), case_sensitive=False),
)
@click.option(
    "-i",
    "--input",
    "input_path",
    type=click.Path(exists=True, path_type=Path),
    help="Input configuration file. If not specified, uses the terminal's default location.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Output file path. If not specified, outputs to stdout.",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Output format (default: yaml).",
)
@click.option(
    "-p",
    "--profile",
    "profile_name",
    type=str,
    default=None,
    help="Profile name to export (iTerm2 only). If not specified, uses the default profile.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def export_config(
    terminal: str,
    input_path: Path | None,
    output_path: Path | None,
    output_format: str,
    profile_name: str | None,
    quiet: bool,
):
    """
    Export a terminal's configuration to CTEC format.

    TERMINAL is the name of the source terminal emulator (e.g., iterm2, ghostty).

    \b
    Examples:
        # Export iTerm2 config to YAML (default)
        console-cowboy export iterm2 -o my-config.yaml

        # Export from a specific file
        console-cowboy export ghostty -i ~/custom/config -o config.json -f json

        # Export to stdout
        console-cowboy export kitty

        # Export a specific iTerm2 profile
        console-cowboy export iterm2 -p "Development" -o dev-config.yaml
    """
    adapter = TerminalRegistry.get(terminal)
    if not adapter:
        raise click.ClickException(f"Unknown terminal: {terminal}")

    # Check if profile option is valid for this terminal
    if profile_name and terminal.lower() not in ("iterm2", "terminal_app"):
        raise click.ClickException(
            f"The --profile option is only supported for iTerm2 and Terminal.app. "
            f"{adapter.display_name} does not have multiple profiles."
        )

    # Determine input path
    if input_path is None:
        input_path = adapter.get_default_config_path()
        if input_path is None:
            raise click.ClickException(
                f"Could not find default config for {terminal}. "
                f"Please specify input file with -i/--input."
            )
        if not quiet:
            click.echo(
                f"Using default config: {input_path}",
                err=True,
            )

    # Parse configuration
    try:
        # Pass profile_name for iTerm2 and Terminal.app, other adapters ignore extra kwargs
        if terminal.lower() in ("iterm2", "terminal_app"):
            ctec = adapter.parse(input_path, profile_name=profile_name)
        else:
            ctec = adapter.parse(input_path)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))
    except ValueError as e:
        # Profile not found error
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to parse {terminal} config: {e}")

    # Serialize to output format
    fmt = OutputFormat(output_format.lower())
    output = CTECSerializer.serialize(ctec, fmt)

    # Write output
    if output_path:
        output_path.write_text(output)
        if not quiet:
            click.echo(f"Exported to {output_path}", err=True)
    else:
        click.echo(output)

    # Print warnings and terminal-specific settings
    if not quiet:
        print_warnings(ctec)
        print_terminal_specific(ctec)


@cli.command(name="import")
@click.argument(
    "input_file",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-t",
    "--terminal",
    "terminal",
    type=click.Choice(get_terminal_choices(), case_sensitive=False),
    required=True,
    help="Target terminal emulator to convert to.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Output file path. If not specified, outputs to stdout.",
)
@click.option(
    "-f",
    "--format",
    "input_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    help="Input format. If not specified, detected from file extension.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def import_config(
    input_file: Path,
    terminal: str,
    output_path: Path | None,
    input_format: str | None,
    quiet: bool,
):
    """
    Import a CTEC configuration into a terminal's native format.

    INPUT_FILE is the path to a CTEC configuration file (.yaml or .json).

    \b
    Examples:
        # Import CTEC config into Ghostty format
        console-cowboy import config.yaml -t ghostty -o ~/.config/ghostty/config

        # Import and output to stdout
        console-cowboy import config.yaml -t alacritty

        # Specify input format explicitly
        console-cowboy import config -t kitty -f yaml
    """
    adapter = TerminalRegistry.get(terminal)
    if not adapter:
        raise click.ClickException(f"Unknown terminal: {terminal}")

    # Determine input format
    fmt = None
    if input_format:
        fmt = OutputFormat(input_format.lower())
    else:
        try:
            fmt = CTECSerializer.detect_format(input_file)
        except ValueError:
            raise click.ClickException(
                "Cannot detect format from extension. Please specify with -f/--format."
            )

    # Parse CTEC configuration
    try:
        ctec = CTECSerializer.read_file(input_file, fmt)
    except Exception as e:
        raise click.ClickException(f"Failed to read CTEC config: {e}")

    # Export to target format
    try:
        output = adapter.export(ctec)
    except Exception as e:
        raise click.ClickException(f"Failed to export to {terminal} format: {e}")

    # Write output
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            click.echo(f"Imported to {output_path}", err=True)
    else:
        click.echo(output)

    # Print warnings
    if not quiet:
        print_warnings(ctec)

        # Check for incompatibilities
        if ctec.source_terminal and ctec.source_terminal != terminal:
            source_specific = ctec.get_terminal_specific(ctec.source_terminal)
            if source_specific:
                click.echo(
                    click.style(
                        f"\nNote: {len(source_specific)} setting(s) from "
                        f"{ctec.source_terminal} could not be converted to {terminal}.",
                        fg="yellow",
                    ),
                    err=True,
                )


@cli.command(name="convert")
@click.argument(
    "input_file",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-f",
    "--from",
    "from_terminal",
    type=click.Choice(get_terminal_choices(), case_sensitive=False),
    required=True,
    help="Source terminal emulator.",
)
@click.option(
    "-t",
    "--to",
    "to_terminal",
    type=click.Choice(get_terminal_choices(), case_sensitive=False),
    required=True,
    help="Target terminal emulator.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Output file path. If not specified, outputs to stdout.",
)
@click.option(
    "-p",
    "--profile",
    "profile_name",
    type=str,
    default=None,
    help="Profile name to convert (iTerm2 source only). If not specified, uses the default profile.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def convert_config(
    input_file: Path,
    from_terminal: str,
    to_terminal: str,
    output_path: Path | None,
    profile_name: str | None,
    quiet: bool,
):
    """
    Convert directly between terminal configuration formats.

    This is a convenience command that combines export and import in one step.

    \b
    Examples:
        # Convert Kitty config to Alacritty
        console-cowboy convert kitty.conf -f kitty -t alacritty -o alacritty.toml

        # Convert iTerm2 plist to Ghostty
        console-cowboy convert com.googlecode.iterm2.plist -f iterm2 -t ghostty

        # Convert a specific iTerm2 profile to Ghostty
        console-cowboy convert com.googlecode.iterm2.plist -f iterm2 -t ghostty -p "Development"
    """
    from_adapter = TerminalRegistry.get(from_terminal)
    to_adapter = TerminalRegistry.get(to_terminal)

    if not from_adapter:
        raise click.ClickException(f"Unknown source terminal: {from_terminal}")
    if not to_adapter:
        raise click.ClickException(f"Unknown target terminal: {to_terminal}")

    # Check if profile option is valid for this terminal
    if profile_name and from_terminal.lower() not in ("iterm2", "terminal_app"):
        raise click.ClickException(
            f"The --profile option is only supported when converting from iTerm2 or Terminal.app. "
            f"{from_adapter.display_name} does not have multiple profiles."
        )

    # Parse source configuration
    try:
        if from_terminal.lower() in ("iterm2", "terminal_app"):
            ctec = from_adapter.parse(input_file, profile_name=profile_name)
        else:
            ctec = from_adapter.parse(input_file)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))
    except ValueError as e:
        # Profile not found error
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to parse {from_terminal} config: {e}")

    # Export to target format
    try:
        output = to_adapter.export(ctec)
    except Exception as e:
        raise click.ClickException(f"Failed to export to {to_terminal} format: {e}")

    # Write output
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            click.echo(
                f"Converted {from_terminal} -> {to_terminal}: {output_path}",
                err=True,
            )
    else:
        click.echo(output)

    # Print warnings and incompatibilities
    if not quiet:
        print_warnings(ctec)

        source_specific = ctec.get_terminal_specific(from_terminal)
        if source_specific:
            click.echo(
                click.style(
                    f"\nNote: {len(source_specific)} {from_terminal}-specific setting(s) "
                    f"could not be converted:",
                    fg="yellow",
                ),
                err=True,
            )
            for setting in source_specific:
                click.echo(
                    click.style(f"  - {setting.key}", fg="yellow"),
                    err=True,
                )


@cli.command(name="info")
@click.argument(
    "input_file",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-t",
    "--terminal",
    "terminal",
    type=click.Choice(get_terminal_choices(), case_sensitive=False),
    help="Terminal type (if parsing native config). If not specified, assumes CTEC format.",
)
def show_info(input_file: Path, terminal: str | None):
    """
    Display information about a configuration file.

    Shows what settings are present and what can/cannot be ported
    to other terminals.

    \b
    Examples:
        # Show info about a CTEC file
        console-cowboy info my-config.toml

        # Show info about a native terminal config
        console-cowboy info ~/.config/kitty/kitty.conf -t kitty
    """
    # Parse the configuration
    if terminal:
        adapter = TerminalRegistry.get(terminal)
        if not adapter:
            raise click.ClickException(f"Unknown terminal: {terminal}")
        try:
            ctec = adapter.parse(input_file)
        except Exception as e:
            raise click.ClickException(f"Failed to parse config: {e}")
    else:
        try:
            fmt = CTECSerializer.detect_format(input_file)
            ctec = CTECSerializer.read_file(input_file, fmt)
        except ValueError:
            raise click.ClickException(
                "Cannot detect format. Use -t to specify terminal type."
            )
        except Exception as e:
            raise click.ClickException(f"Failed to parse CTEC config: {e}")

    # Display information
    click.echo(click.style("Configuration Summary", bold=True, underline=True))
    click.echo()

    if ctec.source_terminal:
        click.echo(f"Source terminal: {click.style(ctec.source_terminal, fg='green')}")

    click.echo(f"CTEC version: {ctec.version}")
    click.echo()

    # Colors
    if ctec.color_scheme:
        click.echo(click.style("Color Scheme:", bold=True))
        scheme = ctec.color_scheme
        color_count = sum(
            1
            for attr in [
                "foreground",
                "background",
                "cursor",
                "black",
                "red",
                "green",
            ]
            if getattr(scheme, attr, None)
        )
        click.echo(f"  Defined colors: {color_count}+")
        if scheme.name:
            click.echo(f"  Name: {scheme.name}")
        click.echo()

    # Font
    if ctec.font:
        click.echo(click.style("Font:", bold=True))
        if ctec.font.family:
            click.echo(f"  Family: {ctec.font.family}")
        if ctec.font.size:
            click.echo(f"  Size: {ctec.font.size}")
        click.echo()

    # Cursor
    if ctec.cursor:
        click.echo(click.style("Cursor:", bold=True))
        if ctec.cursor.style:
            click.echo(f"  Style: {ctec.cursor.style.value}")
        if ctec.cursor.blink is not None:
            click.echo(f"  Blink: {ctec.cursor.blink}")
        click.echo()

    # Window
    if ctec.window:
        click.echo(click.style("Window:", bold=True))
        if ctec.window.columns:
            click.echo(f"  Columns: {ctec.window.columns}")
        if ctec.window.rows:
            click.echo(f"  Rows: {ctec.window.rows}")
        if ctec.window.opacity is not None:
            click.echo(f"  Opacity: {ctec.window.opacity}")
        click.echo()

    # Behavior
    if ctec.behavior:
        click.echo(click.style("Behavior:", bold=True))
        if ctec.behavior.shell:
            click.echo(f"  Shell: {ctec.behavior.shell}")
        if ctec.behavior.scrollback_lines is not None:
            click.echo(f"  Scrollback: {ctec.behavior.scrollback_lines} lines")
        click.echo()

    # Key bindings
    if ctec.key_bindings:
        click.echo(click.style("Key Bindings:", bold=True))
        click.echo(f"  Defined: {len(ctec.key_bindings)}")
        click.echo()

    # Terminal-specific
    if ctec.terminal_specific:
        click.echo(click.style("Terminal-Specific Settings:", bold=True))
        by_terminal: dict[str, int] = {}
        for setting in ctec.terminal_specific:
            by_terminal[setting.terminal] = by_terminal.get(setting.terminal, 0) + 1
        for term, count in by_terminal.items():
            click.echo(f"  {term}: {count} setting(s)")
        click.echo()

    # Warnings
    print_warnings(ctec)


if __name__ == "__main__":
    cli()
