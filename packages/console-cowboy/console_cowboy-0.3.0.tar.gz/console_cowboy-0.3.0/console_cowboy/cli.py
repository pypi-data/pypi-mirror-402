"""
Console Cowboy CLI - Portable Terminal Configuration Manager.

This CLI enables migration of terminal emulator configurations between
different terminal applications using the CTEC (Common Terminal Emulator
Configuration) format as an intermediate representation.

Commands:
    (default): Convert between terminal configurations (implicit convert)
    export: Export a terminal's configuration to CTEC format
    import: Import a CTEC configuration into a terminal's native format
    list: List supported terminal emulators
    info: Display information about a configuration file
"""

import sys
from pathlib import Path

import click

# Import to trigger registration
import console_cowboy.terminals  # noqa: F401
from console_cowboy.ctec import CTEC, CTECSerializer
from console_cowboy.terminals import TerminalRegistry


def get_terminal_choices() -> list[str]:
    """Get list of available terminal names for CLI choices."""
    return TerminalRegistry.get_names()


def unknown_terminal_error(terminal_type: str) -> click.ClickException:
    """Create an error for unknown terminal type with list of valid types."""
    valid_types = ", ".join(sorted(TerminalRegistry.get_names()))
    return click.ClickException(
        f"Unknown terminal type: '{terminal_type}'. "
        f"Valid types are: {valid_types}, ctec"
    )


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


def resolve_source(
    source: str | None,
    source_type: str | None,
    quiet: bool = False,
) -> tuple[str | None, type | None, str | None]:
    """
    Resolve a source argument to content and adapter.

    Args:
        source: The --from argument (terminal name, file path, or "-" for stdin)
        source_type: The --from-type argument (explicit terminal type)
        quiet: Suppress informational output

    Returns:
        Tuple of (content or None, adapter_class or None, source_path or None)
        - content is None when the adapter should read the file directly (for binary formats)
        - adapter_class is None for CTEC format
        - source_path is None for stdin

    Raises:
        click.ClickException: If source cannot be resolved
    """
    if source is None:
        raise click.ClickException("--from is required")

    # Check if source is "-" (stdin)
    if source == "-":
        content = sys.stdin.read()
        source_path = None

        # Determine the adapter for stdin content
        if source_type:
            if source_type.lower() == "ctec":
                return content, None, source_path
            adapter = TerminalRegistry.get(source_type)
            if not adapter:
                raise unknown_terminal_error(source_type)
            return content, adapter, source_path

        # Try to detect the type from content
        if TerminalRegistry.is_ctec_file(content):
            return content, None, source_path

        adapter = TerminalRegistry.detect_terminal_type(content)
        if adapter:
            return content, adapter, source_path

        raise click.ClickException(
            "Could not detect config format from stdin. "
            "Please specify --from-type as 'ctec' or a terminal name."
        )

    # Check if source is a known terminal name
    adapter = TerminalRegistry.get(source)
    if adapter:
        # Find the terminal's config file
        config_path = adapter.get_default_config_path()
        if config_path is None:
            raise click.ClickException(
                f"Could not find default config for {source}. "
                "Please provide a file path instead."
            )
        if not quiet:
            click.echo(f"Using {source} config: {config_path}", err=True)
        # Return None for content - let the adapter read the file directly
        # This handles binary formats like plist
        return None, adapter, str(config_path)

    # Treat as file path
    path = Path(source)
    if not path.exists():
        raise click.ClickException(f"File not found: {source}")
    source_path = source

    # If explicit type is provided, let the adapter read the file
    if source_type:
        if source_type.lower() == "ctec":
            # CTEC is always text, safe to read
            content = path.read_text()
            return content, None, source_path
        adapter = TerminalRegistry.get(source_type)
        if not adapter:
            raise unknown_terminal_error(source_type)
        # Return None for content - let the adapter read the file directly
        return None, adapter, source_path

    # No explicit type - try to detect from content
    # First try to read as text for detection
    try:
        content = path.read_text()
    except UnicodeDecodeError:
        # Binary file - try binary format adapters
        # For now, try iTerm2 and Terminal.app which use binary plist
        for binary_adapter_name in ["iterm2", "terminal_app"]:
            binary_adapter = TerminalRegistry.get(binary_adapter_name)
            if binary_adapter:
                try:
                    # Try parsing - if it works, use this adapter
                    binary_adapter.parse(path)
                    return None, binary_adapter, source_path
                except Exception:
                    continue
        raise click.ClickException(
            f"Could not read '{source}' as text and it doesn't appear to be a known binary format. "
            "Please specify --from-type."
        )

    # Try to detect the type from text content
    if TerminalRegistry.is_ctec_file(content):
        return content, None, source_path

    adapter = TerminalRegistry.detect_terminal_type(content)
    if adapter:
        return content, adapter, source_path

    raise click.ClickException(
        f"Could not detect config format from '{source}'. "
        "Please specify --from-type as 'ctec' or a terminal name."
    )


def resolve_destination(
    dest: str | None,
    dest_type: str | None,
) -> tuple[Path | None, type | None]:
    """
    Resolve a destination argument.

    Args:
        dest: The --to argument (terminal name, file path, or "-" for stdout)
        dest_type: The --to-type argument (explicit terminal type)

    Returns:
        Tuple of (output_path or None for stdout, adapter_class or None for CTEC)

    Raises:
        click.ClickException: If destination cannot be resolved
    """
    # Handle --to-type without --to (output to stdout)
    if dest is None and dest_type:
        if dest_type.lower() == "ctec":
            return None, None  # CTEC to stdout
        adapter = TerminalRegistry.get(dest_type)
        if not adapter:
            raise unknown_terminal_error(dest_type)
        return None, adapter

    if dest is None:
        # No --to means output CTEC to stdout
        return None, None

    # Check if dest is "-" (stdout)
    if dest == "-":
        if dest_type:
            if dest_type.lower() == "ctec":
                return None, None
            adapter = TerminalRegistry.get(dest_type)
            if not adapter:
                raise unknown_terminal_error(dest_type)
            return None, adapter
        # Default to CTEC when outputting to stdout
        return None, None

    # Check if dest is a known terminal name
    adapter = TerminalRegistry.get(dest)
    if adapter:
        # Get the terminal's config path
        config_path = TerminalRegistry.get_default_config_path_for_write(dest)
        if config_path is None:
            raise click.ClickException(f"Could not determine config path for {dest}.")
        return config_path, adapter

    # Treat as file path
    path = Path(dest)

    # Determine output type
    if dest_type:
        if dest_type.lower() == "ctec":
            return path, None
        adapter = TerminalRegistry.get(dest_type)
        if not adapter:
            raise unknown_terminal_error(dest_type)
        return path, adapter

    # Try to infer from file extension
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return path, None  # CTEC
    if suffix == ".lua":
        return path, TerminalRegistry.get("wezterm")
    if suffix == ".toml":
        return path, TerminalRegistry.get("alacritty")
    if suffix in (".plist", ".itermcolors"):
        return path, TerminalRegistry.get("iterm2")
    if suffix == ".terminal":
        return path, TerminalRegistry.get("terminal_app")
    if suffix == ".conf":
        return path, TerminalRegistry.get("kitty")

    # Default to CTEC for unknown extensions
    return path, None


@click.group(invoke_without_command=True)
@click.option(
    "--from",
    "source",
    type=str,
    help="Source: terminal name (e.g., 'iterm2'), file path, or '-' for stdin.",
)
@click.option(
    "--from-type",
    "source_type",
    type=str,
    help="Explicit source type: 'ctec' or a terminal name.",
)
@click.option(
    "--to",
    "dest",
    type=str,
    help="Destination: terminal name, file path, or '-' for stdout.",
)
@click.option(
    "--to-type",
    "dest_type",
    type=str,
    help="Explicit destination type: 'ctec' or a terminal name.",
)
@click.option(
    "--profile",
    "profile_name",
    type=str,
    default=None,
    help="Profile name (iTerm2/Terminal.app only).",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
@click.version_option()
@click.pass_context
def cli(
    ctx,
    source: str | None,
    source_type: str | None,
    dest: str | None,
    dest_type: str | None,
    profile_name: str | None,
    quiet: bool,
):
    """
    Console Cowboy - Hop terminals like you hop Linux distributions.

    A tool for making terminal configurations portable across different
    terminal emulators. Export your settings from one terminal and import
    them into another.

    \b
    Examples:
        # Convert iTerm2 settings to Ghostty config
        console-cowboy --from iterm2 --to ghostty

        # Convert a config file to another terminal
        console-cowboy --from path/to/config --to ghostty

        # Export iTerm2 to CTEC (stdout)
        console-cowboy --from iterm2

        # Export to specific format
        console-cowboy --from wezterm --to-type alacritty

        # Read from stdin
        cat config | console-cowboy --from - --from-type ghostty --to alacritty

    Supported terminals: iTerm2, Ghostty, Alacritty, Kitty, Wezterm, VSCode, Terminal.app
    """
    # If a subcommand is invoked, let it handle everything
    if ctx.invoked_subcommand is not None:
        return

    # If no arguments provided, show help
    if source is None and dest is None and dest_type is None:
        click.echo(ctx.get_help())
        return

    # Validate: need --from
    if source is None:
        raise click.ClickException("--from is required")

    # Validate: --to without --from is an error (unless we have --to-type for the output)
    # Actually, the instructions say: "If there is a 'to' but not a 'from', it errors"
    # But we already checked source is required above.

    # Resolve source
    content, source_adapter, source_path = resolve_source(source, source_type, quiet)

    # Parse source into CTEC
    if source_adapter is None:
        # Source is CTEC
        if content is None:
            raise click.ClickException("Cannot read CTEC from binary file")
        try:
            ctec = CTECSerializer.from_yaml(content)
        except Exception as e:
            raise click.ClickException(f"Failed to parse CTEC: {e}")
    else:
        # Source is terminal config
        try:
            # Build kwargs - only pass content if it's not None
            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if source_adapter.name in ("iterm2", "terminal_app") and profile_name:
                kwargs["profile_name"] = profile_name
            ctec = source_adapter.parse(source_path or "stdin", **kwargs)
        except FileNotFoundError as e:
            raise click.ClickException(str(e))
        except ValueError as e:
            raise click.ClickException(str(e))
        except Exception as e:
            raise click.ClickException(
                f"Failed to parse {source_adapter.name} config: {e}"
            )

    # Resolve destination
    output_path, dest_adapter = resolve_destination(dest, dest_type)

    # Generate output
    if dest_adapter is None:
        # Output as CTEC (YAML only)
        output = CTECSerializer.to_yaml(ctec)
    else:
        # Output as terminal config
        try:
            output = dest_adapter.export(ctec)
        except Exception as e:
            raise click.ClickException(f"Failed to export to {dest_adapter.name}: {e}")

    # Write output
    if output_path is None:
        # stdout
        click.echo(output)
    else:
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            if dest_adapter:
                click.echo(
                    f"Wrote {dest_adapter.name} config to {output_path}", err=True
                )
            else:
                click.echo(f"Wrote CTEC to {output_path}", err=True)

    # Print warnings
    if not quiet:
        print_warnings(ctec)
        if source_adapter and dest_adapter:
            # Show terminal-specific settings that couldn't be converted
            source_specific = ctec.get_terminal_specific(source_adapter.name)
            if source_specific:
                click.echo(
                    click.style(
                        f"\nNote: {len(source_specific)} {source_adapter.name}-specific "
                        f"setting(s) could not be converted:",
                        fg="yellow",
                    ),
                    err=True,
                )
                for setting in source_specific:
                    click.echo(
                        click.style(f"  - {setting.key}", fg="yellow"),
                        err=True,
                    )


@cli.command(name="list")
def list_terminals():
    """
    List all supported terminal emulators.

    Shows terminal names that can be used with --from and --to.
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
@click.option(
    "--from",
    "source",
    type=str,
    required=True,
    help="Source: terminal name (e.g., 'iterm2'), file path, or '-' for stdin.",
)
@click.option(
    "--from-type",
    "source_type",
    type=str,
    help="Explicit source type (terminal name).",
)
@click.option(
    "--to",
    "dest",
    type=str,
    help="Output file path or '-' for stdout. Defaults to stdout.",
)
@click.option(
    "--profile",
    "profile_name",
    type=str,
    default=None,
    help="Profile name (iTerm2/Terminal.app only).",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def export_config(
    source: str,
    source_type: str | None,
    dest: str | None,
    profile_name: str | None,
    quiet: bool,
):
    """
    Export a terminal's configuration to CTEC format (YAML).

    The export command converts terminal-specific configs to the portable
    CTEC format. Output is always CTEC YAML.

    \b
    Examples:
        # Export iTerm2 config to stdout
        console-cowboy export --from iterm2

        # Export from a specific file
        console-cowboy export --from ~/.config/ghostty/config --to config.yaml

        # Export a specific iTerm2 profile
        console-cowboy export --from iterm2 --profile "Development"
    """
    # Resolve source
    content, source_adapter, source_path = resolve_source(source, source_type, quiet)

    # For export, source must be a terminal (not CTEC)
    if source_adapter is None:
        raise click.ClickException(
            "Export requires a terminal config as source, not CTEC. "
            "Use --from with a terminal name or specify --from-type."
        )

    # Parse source
    try:
        # Build kwargs - only pass content if it's not None
        kwargs = {}
        if content is not None:
            kwargs["content"] = content
        if source_adapter.name in ("iterm2", "terminal_app") and profile_name:
            kwargs["profile_name"] = profile_name
        ctec = source_adapter.parse(source_path or "stdin", **kwargs)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))
    except ValueError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Failed to parse {source_adapter.name} config: {e}")

    # Serialize to YAML (only YAML for CTEC)
    output = CTECSerializer.to_yaml(ctec)

    # Write output
    if dest is None or dest == "-":
        click.echo(output)
    else:
        output_path = Path(dest)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            click.echo(f"Exported to {output_path}", err=True)

    # Print warnings
    if not quiet:
        print_warnings(ctec)
        print_terminal_specific(ctec)


@cli.command(name="import")
@click.option(
    "--from",
    "source",
    type=str,
    required=True,
    help="CTEC file path or '-' for stdin.",
)
@click.option(
    "--to",
    "dest",
    type=str,
    help="Destination: terminal name, file path, or '-' for stdout.",
)
@click.option(
    "--to-type",
    "dest_type",
    type=str,
    help="Explicit destination type (terminal name).",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def import_config(
    source: str,
    dest: str | None,
    dest_type: str | None,
    quiet: bool,
):
    """
    Import a CTEC configuration into a terminal's native format.

    The import command converts CTEC YAML to terminal-specific config.

    \b
    Examples:
        # Import CTEC to Ghostty's default location
        console-cowboy import --from config.yaml --to ghostty

        # Import to a specific file
        console-cowboy import --from config.yaml --to ~/.config/alacritty/alacritty.toml --to-type alacritty

        # Import from stdin
        cat config.yaml | console-cowboy import --from - --to ghostty
    """
    # Read source (must be CTEC)
    if source == "-":
        content = sys.stdin.read()
    else:
        path = Path(source)
        if not path.exists():
            raise click.ClickException(f"File not found: {source}")
        content = path.read_text()

    # Parse CTEC
    try:
        ctec = CTECSerializer.from_yaml(content)
    except Exception as e:
        raise click.ClickException(f"Failed to parse CTEC: {e}")

    # Resolve destination
    output_path, dest_adapter = resolve_destination(dest, dest_type)

    # For import, destination must be a terminal (not CTEC)
    if dest_adapter is None:
        raise click.ClickException(
            "Import requires a terminal as destination. "
            "Use --to with a terminal name or specify --to-type."
        )

    # Export to terminal format
    try:
        output = dest_adapter.export(ctec)
    except Exception as e:
        raise click.ClickException(f"Failed to export to {dest_adapter.name}: {e}")

    # Write output
    if output_path is None:
        click.echo(output)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            click.echo(f"Imported to {output_path}", err=True)

    # Print warnings
    if not quiet:
        print_warnings(ctec)

        # Check for incompatibilities
        if ctec.source_terminal and ctec.source_terminal != dest_adapter.name:
            source_specific = ctec.get_terminal_specific(ctec.source_terminal)
            if source_specific:
                click.echo(
                    click.style(
                        f"\nNote: {len(source_specific)} setting(s) from "
                        f"{ctec.source_terminal} could not be converted to {dest_adapter.name}.",
                        fg="yellow",
                    ),
                    err=True,
                )


@cli.command(name="convert")
@click.option(
    "--from",
    "source",
    type=str,
    required=True,
    help="Source: terminal name, file path, or '-' for stdin.",
)
@click.option(
    "--from-type",
    "source_type",
    type=str,
    help="Explicit source type: 'ctec' or a terminal name.",
)
@click.option(
    "--to",
    "dest",
    type=str,
    required=True,
    help="Destination: terminal name, file path, or '-' for stdout.",
)
@click.option(
    "--to-type",
    "dest_type",
    type=str,
    help="Explicit destination type: 'ctec' or a terminal name.",
)
@click.option(
    "--profile",
    "profile_name",
    type=str,
    default=None,
    help="Profile name (iTerm2/Terminal.app source only).",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress warnings and informational output.",
)
def convert_config(
    source: str,
    source_type: str | None,
    dest: str,
    dest_type: str | None,
    profile_name: str | None,
    quiet: bool,
):
    """
    Convert directly between terminal configuration formats.

    This is equivalent to using the default command with both --from and --to.

    \b
    Examples:
        # Convert Kitty config to Alacritty
        console-cowboy convert --from kitty --to alacritty

        # Convert a specific file
        console-cowboy convert --from config.lua --from-type wezterm --to ghostty

        # Convert a specific iTerm2 profile
        console-cowboy convert --from iterm2 --profile "Development" --to ghostty
    """
    # This is essentially the same as the main command with both --from and --to
    # Resolve source
    content, source_adapter, source_path = resolve_source(source, source_type, quiet)

    # Parse source into CTEC
    if source_adapter is None:
        # Source is CTEC
        if content is None:
            raise click.ClickException("Cannot read CTEC from binary file")
        try:
            ctec = CTECSerializer.from_yaml(content)
        except Exception as e:
            raise click.ClickException(f"Failed to parse CTEC: {e}")
    else:
        # Source is terminal config
        try:
            # Build kwargs - only pass content if it's not None
            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            if source_adapter.name in ("iterm2", "terminal_app") and profile_name:
                kwargs["profile_name"] = profile_name
            ctec = source_adapter.parse(source_path or "stdin", **kwargs)
        except FileNotFoundError as e:
            raise click.ClickException(str(e))
        except ValueError as e:
            raise click.ClickException(str(e))
        except Exception as e:
            raise click.ClickException(
                f"Failed to parse {source_adapter.name} config: {e}"
            )

    # Resolve destination
    output_path, dest_adapter = resolve_destination(dest, dest_type)

    # Generate output
    if dest_adapter is None:
        # Output as CTEC (YAML only)
        output = CTECSerializer.to_yaml(ctec)
    else:
        # Output as terminal config
        try:
            output = dest_adapter.export(ctec)
        except Exception as e:
            raise click.ClickException(f"Failed to export to {dest_adapter.name}: {e}")

    # Write output
    if output_path is None:
        click.echo(output)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        if not quiet:
            if source_adapter and dest_adapter:
                click.echo(
                    f"Converted {source_adapter.name} -> {dest_adapter.name}: {output_path}",
                    err=True,
                )
            elif dest_adapter:
                click.echo(f"Converted to {dest_adapter.name}: {output_path}", err=True)
            else:
                click.echo(f"Converted to CTEC: {output_path}", err=True)

    # Print warnings
    if not quiet:
        print_warnings(ctec)
        if source_adapter and dest_adapter:
            source_specific = ctec.get_terminal_specific(source_adapter.name)
            if source_specific:
                click.echo(
                    click.style(
                        f"\nNote: {len(source_specific)} {source_adapter.name}-specific "
                        f"setting(s) could not be converted:",
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
@click.option(
    "--from",
    "source",
    type=str,
    required=True,
    help="Config file path, terminal name, or '-' for stdin.",
)
@click.option(
    "--from-type",
    "source_type",
    type=str,
    help="Explicit source type: 'ctec' or a terminal name.",
)
def show_info(source: str, source_type: str | None):
    """
    Display information about a configuration file.

    Shows what settings are present and what can/cannot be ported
    to other terminals.

    \b
    Examples:
        # Show info about a CTEC file
        console-cowboy info --from my-config.yaml

        # Show info about a terminal's config
        console-cowboy info --from ghostty
    """
    # Resolve source
    content, source_adapter, source_path = resolve_source(
        source, source_type, quiet=True
    )

    # Parse configuration
    if source_adapter is None:
        if content is None:
            raise click.ClickException("Cannot read CTEC from binary file")
        try:
            ctec = CTECSerializer.from_yaml(content)
        except Exception as e:
            raise click.ClickException(f"Failed to parse CTEC: {e}")
    else:
        try:
            # Build kwargs - only pass content if it's not None
            kwargs = {}
            if content is not None:
                kwargs["content"] = content
            ctec = source_adapter.parse(source_path or "stdin", **kwargs)
        except Exception as e:
            raise click.ClickException(f"Failed to parse config: {e}")

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
