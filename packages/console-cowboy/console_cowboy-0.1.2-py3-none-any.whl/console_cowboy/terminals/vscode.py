"""
VSCode terminal configuration adapter.

VSCode stores terminal settings in its settings.json file, typically at:
- macOS: ~/Library/Application Support/Code/User/settings.json
- Linux: ~/.config/Code/User/settings.json
- Windows: %APPDATA%/Code/User/settings.json

Terminal colors are stored inside the workbench.colorCustomizations object.
"""

import json
from pathlib import Path

import click

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    FontWeight,
    ScrollConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter


class VSCodeAdapter(TerminalAdapter):
    """
    Adapter for Visual Studio Code integrated terminal.

    VSCode uses JSON for configuration with terminal settings at
    terminal.integrated.* keys and colors in workbench.colorCustomizations.
    """

    name = "vscode"
    display_name = "Visual Studio Code"
    description = "Microsoft's code editor with integrated terminal"
    config_extensions = [".json"]
    default_config_paths = [
        # macOS
        "Library/Application Support/Code/User/settings.json",
        # Linux
        ".config/Code/User/settings.json",
        # Also check VSCode Insiders
        "Library/Application Support/Code - Insiders/User/settings.json",
        ".config/Code - Insiders/User/settings.json",
    ]

    # Cursor style mapping (VSCode uses 'line' for beam cursor)
    CURSOR_STYLE_MAP = {
        "block": CursorStyle.BLOCK,
        "line": CursorStyle.BEAM,
        "underline": CursorStyle.UNDERLINE,
    }

    CURSOR_STYLE_REVERSE_MAP = {v: k for k, v in CURSOR_STYLE_MAP.items()}

    # Color key mapping from VSCode (inside workbench.colorCustomizations) to CTEC
    COLOR_KEY_MAP = {
        "terminal.foreground": "foreground",
        "terminal.background": "background",
        "terminal.selectionBackground": "selection",
        "terminal.selectionForeground": "selection_text",
        "terminalCursor.foreground": "cursor",
        "terminalCursor.background": "cursor_text",
        # ANSI colors
        "terminal.ansiBlack": "black",
        "terminal.ansiRed": "red",
        "terminal.ansiGreen": "green",
        "terminal.ansiYellow": "yellow",
        "terminal.ansiBlue": "blue",
        "terminal.ansiMagenta": "magenta",
        "terminal.ansiCyan": "cyan",
        "terminal.ansiWhite": "white",
        "terminal.ansiBrightBlack": "bright_black",
        "terminal.ansiBrightRed": "bright_red",
        "terminal.ansiBrightGreen": "bright_green",
        "terminal.ansiBrightYellow": "bright_yellow",
        "terminal.ansiBrightBlue": "bright_blue",
        "terminal.ansiBrightMagenta": "bright_magenta",
        "terminal.ansiBrightCyan": "bright_cyan",
        "terminal.ansiBrightWhite": "bright_white",
    }

    COLOR_KEY_REVERSE_MAP = {v: k for k, v in COLOR_KEY_MAP.items()}

    # Keys we explicitly handle (not stored as terminal_specific)
    _RECOGNIZED_KEYS = {
        "terminal.integrated.fontFamily",
        "terminal.integrated.fontSize",
        "terminal.integrated.fontWeight",
        "terminal.integrated.lineHeight",
        "terminal.integrated.letterSpacing",
        "terminal.integrated.fontLigatures",
        "terminal.integrated.cursorStyle",
        "terminal.integrated.cursorBlinking",
        "terminal.integrated.scrollback",
        "terminal.integrated.copyOnSelection",
        "terminal.integrated.confirmOnExit",
        "workbench.colorCustomizations",
    }

    @classmethod
    def _parse_font_weight(cls, value: str | int) -> FontWeight | None:
        """Convert VSCode font weight to CTEC FontWeight."""
        if value is None:
            return None
        try:
            if isinstance(value, int):
                # Direct numeric weight
                return FontWeight(value)
            # String weight name
            return FontWeight.from_string(str(value))
        except ValueError:
            return None

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse VSCode settings.json containing terminal configuration."""
        ctec = CTEC(source_terminal="vscode")

        # Load JSON content
        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        # Parse font settings
        font = FontConfig()
        font_modified = False

        if "terminal.integrated.fontFamily" in data:
            font.family = data["terminal.integrated.fontFamily"]
            font_modified = True

        if "terminal.integrated.fontSize" in data:
            try:
                font.size = float(data["terminal.integrated.fontSize"])
                font_modified = True
            except (ValueError, TypeError):
                ctec.add_warning(
                    f"Invalid fontSize: {data['terminal.integrated.fontSize']}"
                )

        if "terminal.integrated.fontWeight" in data:
            weight = cls._parse_font_weight(data["terminal.integrated.fontWeight"])
            if weight:
                font.weight = weight
                font_modified = True
            else:
                ctec.add_warning(
                    f"Invalid fontWeight: {data['terminal.integrated.fontWeight']}"
                )

        if "terminal.integrated.lineHeight" in data:
            try:
                font.line_height = float(data["terminal.integrated.lineHeight"])
                font_modified = True
            except (ValueError, TypeError):
                ctec.add_warning(
                    f"Invalid lineHeight: {data['terminal.integrated.lineHeight']}"
                )

        if "terminal.integrated.letterSpacing" in data:
            try:
                # letterSpacing is in pixels, convert to cell_width multiplier
                # Approximate: +1px spacing ~ +0.1 cell_width
                spacing = float(data["terminal.integrated.letterSpacing"])
                font.cell_width = 1.0 + (spacing / 10.0)
                font_modified = True
            except (ValueError, TypeError):
                ctec.add_warning(
                    f"Invalid letterSpacing: {data['terminal.integrated.letterSpacing']}"
                )

        if "terminal.integrated.fontLigatures" in data:
            ligatures_val = data["terminal.integrated.fontLigatures"]
            # Can be boolean or CSS font-feature-settings string
            if isinstance(ligatures_val, bool):
                font.ligatures = ligatures_val
            else:
                # String means enabled with specific features
                font.ligatures = True
                ctec.add_terminal_specific(
                    "vscode", "terminal.integrated.fontLigatures", ligatures_val
                )
            font_modified = True

        if font_modified:
            ctec.font = font

        # Parse cursor settings
        cursor = CursorConfig()
        cursor_modified = False

        if "terminal.integrated.cursorStyle" in data:
            style_str = data["terminal.integrated.cursorStyle"]
            cursor.style = cls.CURSOR_STYLE_MAP.get(style_str, CursorStyle.BLOCK)
            cursor_modified = True

        if "terminal.integrated.cursorBlinking" in data:
            cursor.blink = bool(data["terminal.integrated.cursorBlinking"])
            cursor_modified = True

        if cursor_modified:
            ctec.cursor = cursor

        # Parse colors from workbench.colorCustomizations
        if "workbench.colorCustomizations" in data:
            color_customs = data["workbench.colorCustomizations"]
            if isinstance(color_customs, dict):
                scheme = ColorScheme()
                scheme_modified = False

                for vscode_key, ctec_attr in cls.COLOR_KEY_MAP.items():
                    if vscode_key in color_customs:
                        try:
                            color = normalize_color(color_customs[vscode_key])
                            setattr(scheme, ctec_attr, color)
                            scheme_modified = True
                        except (ValueError, TypeError):
                            ctec.add_warning(f"Invalid color for {vscode_key}")

                if scheme_modified:
                    ctec.color_scheme = scheme

        # Parse scroll settings
        if "terminal.integrated.scrollback" in data:
            try:
                lines = int(data["terminal.integrated.scrollback"])
                ctec.scroll = ScrollConfig.from_lines(lines)
            except (ValueError, TypeError):
                ctec.add_warning(
                    f"Invalid scrollback: {data['terminal.integrated.scrollback']}"
                )

        # Parse behavior settings
        behavior = BehaviorConfig()
        behavior_modified = False

        if "terminal.integrated.copyOnSelection" in data:
            behavior.copy_on_select = bool(data["terminal.integrated.copyOnSelection"])
            behavior_modified = True

        if "terminal.integrated.confirmOnExit" in data:
            confirm_val = data["terminal.integrated.confirmOnExit"]
            # VSCode uses "never", "always", "hasChildProcesses"
            behavior.confirm_close = confirm_val != "never"
            behavior_modified = True

        if behavior_modified:
            ctec.behavior = behavior

        # Store VSCode-specific settings that have no CTEC equivalent
        for key in data:
            if (
                key.startswith("terminal.integrated.")
                and key not in cls._RECOGNIZED_KEYS
            ):
                ctec.add_terminal_specific("vscode", key, data[key])

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """
        Export CTEC to VSCode settings.json format.

        Returns a JSON object containing only terminal-related settings.
        Users should merge this into their existing settings.json.

        Note: Colors are exported inside workbench.colorCustomizations.
        """
        result = {}

        # Export font settings
        if ctec.font:
            if ctec.font.family:
                result["terminal.integrated.fontFamily"] = ctec.font.family
            if ctec.font.size:
                result["terminal.integrated.fontSize"] = ctec.font.size
            if ctec.font.weight:
                result["terminal.integrated.fontWeight"] = ctec.font.weight.value
            if ctec.font.line_height:
                result["terminal.integrated.lineHeight"] = ctec.font.line_height
            if ctec.font.cell_width and ctec.font.cell_width != 1.0:
                # Convert cell_width back to letterSpacing (approximate)
                spacing = int((ctec.font.cell_width - 1.0) * 10)
                result["terminal.integrated.letterSpacing"] = spacing
            if ctec.font.ligatures is not None:
                result["terminal.integrated.fontLigatures"] = ctec.font.ligatures

        # Export cursor settings
        if ctec.cursor:
            if ctec.cursor.style:
                result["terminal.integrated.cursorStyle"] = (
                    cls.CURSOR_STYLE_REVERSE_MAP.get(ctec.cursor.style, "block")
                )
            if ctec.cursor.blink is not None:
                result["terminal.integrated.cursorBlinking"] = ctec.cursor.blink

        # Export colors inside workbench.colorCustomizations
        if ctec.color_scheme:
            color_customs = {}
            for ctec_attr, vscode_key in cls.COLOR_KEY_REVERSE_MAP.items():
                color = getattr(ctec.color_scheme, ctec_attr, None)
                if color:
                    color_customs[vscode_key] = color.to_hex()

            if color_customs:
                result["workbench.colorCustomizations"] = color_customs

        # Export scroll settings
        if ctec.scroll:
            lines = ctec.scroll.get_effective_lines(default=1000, max_lines=100000)
            result["terminal.integrated.scrollback"] = lines

        # Export behavior settings
        if ctec.behavior:
            if ctec.behavior.copy_on_select is not None:
                result["terminal.integrated.copyOnSelection"] = (
                    ctec.behavior.copy_on_select
                )
            if ctec.behavior.confirm_close is not None:
                result["terminal.integrated.confirmOnExit"] = (
                    "always" if ctec.behavior.confirm_close else "never"
                )

        # Restore VSCode-specific settings
        for setting in ctec.get_terminal_specific("vscode"):
            result[setting.key] = setting.value

        # Print informational message to stderr
        click.echo(
            click.style("\nVSCode Export Notes:", fg="cyan", bold=True),
            err=True,
        )
        click.echo(
            click.style(
                "  This output contains terminal settings that should be merged\n"
                "  into your VSCode settings.json file. You can either:\n"
                "    1. Copy these settings manually into your settings.json\n"
                "    2. Use 'Code > Preferences > Settings' (JSON mode) to merge\n"
                "\n"
                "  Note: Colors are inside 'workbench.colorCustomizations'.\n"
                "  If you already have colorCustomizations, merge the terminal\n"
                "  colors into your existing object.",
                dim=True,
            ),
            err=True,
        )

        return json.dumps(result, indent=2)
