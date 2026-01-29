"""
Ghostty configuration adapter.

Ghostty uses a simple key=value configuration format stored in
~/.config/ghostty/config
"""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    QuickTerminalConfig,
    QuickTerminalPosition,
    QuickTerminalScreen,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter


class GhosttyAdapter(TerminalAdapter):
    """
    Adapter for Ghostty terminal emulator.

    Ghostty uses a simple key=value configuration format with support
    for comments (lines starting with #).
    """

    name = "ghostty"
    display_name = "Ghostty"
    description = "Fast, native terminal emulator written in Zig"
    config_extensions = []
    default_config_paths = [
        ".config/ghostty/config",
    ]

    # Mapping of Ghostty color keys to CTEC
    COLOR_KEY_MAP = {
        "foreground": "foreground",
        "background": "background",
        "cursor-color": "cursor",
        "cursor-text": "cursor_text",
        "selection-foreground": "selection_text",
        "selection-background": "selection",
        "palette": None,  # Handled specially
    }

    # Cursor style mapping
    CURSOR_STYLE_MAP = {
        "block": CursorStyle.BLOCK,
        "bar": CursorStyle.BEAM,
        "underline": CursorStyle.UNDERLINE,
    }

    CURSOR_STYLE_REVERSE_MAP = {v: k for k, v in CURSOR_STYLE_MAP.items()}

    # Quick terminal position mapping
    QUICK_TERMINAL_POSITION_MAP = {
        "top": QuickTerminalPosition.TOP,
        "bottom": QuickTerminalPosition.BOTTOM,
        "left": QuickTerminalPosition.LEFT,
        "right": QuickTerminalPosition.RIGHT,
    }

    QUICK_TERMINAL_POSITION_REVERSE_MAP = {
        v: k for k, v in QUICK_TERMINAL_POSITION_MAP.items()
    }

    # Quick terminal screen mapping
    QUICK_TERMINAL_SCREEN_MAP = {
        "main": QuickTerminalScreen.MAIN,
        "mouse": QuickTerminalScreen.MOUSE,
        "macos-menu-bar": QuickTerminalScreen.MACOS_MENU_BAR,
    }

    QUICK_TERMINAL_SCREEN_REVERSE_MAP = {
        v: k for k, v in QUICK_TERMINAL_SCREEN_MAP.items()
    }

    @classmethod
    def _parse_palette_color(cls, index: int, value: str, scheme: ColorScheme) -> None:
        """Parse a palette color from Ghostty format (index=color)."""
        color = normalize_color(value)
        color_names = [
            "black",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
            "bright_black",
            "bright_red",
            "bright_green",
            "bright_yellow",
            "bright_blue",
            "bright_magenta",
            "bright_cyan",
            "bright_white",
        ]
        if 0 <= index < len(color_names):
            setattr(scheme, color_names[index], color)

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse a Ghostty configuration file."""
        ctec = CTEC(source_terminal="ghostty")
        scheme = ColorScheme()
        font = FontConfig()
        cursor = CursorConfig()
        window = WindowConfig()
        behavior = BehaviorConfig()
        quick_terminal = QuickTerminalConfig()

        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                ctec.add_warning(f"Invalid line (no '='): {line}")
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Parse color settings
            if key == "foreground":
                scheme.foreground = normalize_color(value)
            elif key == "background":
                scheme.background = normalize_color(value)
            elif key == "cursor-color":
                scheme.cursor = normalize_color(value)
            elif key == "cursor-text":
                scheme.cursor_text = normalize_color(value)
            elif key == "selection-foreground":
                scheme.selection_text = normalize_color(value)
            elif key == "selection-background":
                scheme.selection = normalize_color(value)
            elif key == "palette":
                # Format: index=color (e.g., "0=#1d1f21")
                if "=" in value:
                    idx_str, color_str = value.split("=", 1)
                    try:
                        idx = int(idx_str)
                        cls._parse_palette_color(idx, color_str, scheme)
                    except ValueError:
                        ctec.add_warning(f"Invalid palette entry: {value}")

            # Parse font settings
            elif key == "font-family":
                font.family = value
            elif key == "font-size":
                try:
                    font.size = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid font-size: {value}")
            elif key == "font-family-bold":
                font.bold_font = value
            elif key == "font-family-italic":
                font.italic_font = value
            elif key == "adjust-cell-height":
                try:
                    font.line_height = 1.0 + float(value) / 100
                except ValueError:
                    ctec.add_warning(f"Invalid adjust-cell-height: {value}")
            elif key == "adjust-cell-width":
                try:
                    # Handle both "5" and "5%" formats
                    val_str = value.rstrip("%")
                    font.cell_width = 1.0 + float(val_str) / 100
                except ValueError:
                    ctec.add_warning(f"Invalid adjust-cell-width: {value}")
            elif key == "font-family-bold-italic":
                font.bold_italic_font = value

            # Parse cursor settings
            elif key == "cursor-style":
                cursor.style = cls.CURSOR_STYLE_MAP.get(
                    value.lower(), CursorStyle.BLOCK
                )
            elif key == "cursor-style-blink":
                cursor.blink = value.lower() == "true"

            # Parse window settings
            elif key == "window-width":
                try:
                    window.columns = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid window-width: {value}")
            elif key == "window-height":
                try:
                    window.rows = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid window-height: {value}")
            elif key == "background-opacity":
                try:
                    window.opacity = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid background-opacity: {value}")
            elif key == "background-blur-radius":
                try:
                    window.blur = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid background-blur-radius: {value}")
            elif key == "window-padding-x":
                try:
                    window.padding_horizontal = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid window-padding-x: {value}")
            elif key == "window-padding-y":
                try:
                    window.padding_vertical = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid window-padding-y: {value}")
            elif key == "window-decoration":
                window.decorations = value.lower() != "none"
            elif key == "fullscreen":
                if value.lower() == "true":
                    window.startup_mode = "fullscreen"
            elif key == "window-title-show-all":
                window.dynamic_title = value.lower() == "true"

            # Parse behavior settings
            elif key == "command":
                behavior.shell = value
            elif key == "working-directory":
                behavior.working_directory = value
            elif key == "scrollback-limit":
                try:
                    # Ghostty uses bytes, not lines - convert to ScrollConfig
                    byte_count = int(value)
                    ctec.scroll = ScrollConfig.from_bytes(byte_count)
                except ValueError:
                    ctec.add_warning(f"Invalid scrollback-limit: {value}")
            elif key == "mouse-hide-while-typing":
                # Not directly mappable, store as terminal-specific
                ctec.add_terminal_specific("ghostty", key, value.lower() == "true")
            elif key == "copy-on-select":
                behavior.copy_on_select = value.lower() == "true"
            elif key == "confirm-close-surface":
                behavior.confirm_close = value.lower() == "true"

            # Parse quick terminal settings
            elif key == "quick-terminal-position":
                quick_terminal.enabled = True
                quick_terminal.position = cls.QUICK_TERMINAL_POSITION_MAP.get(
                    value.lower(), QuickTerminalPosition.TOP
                )
            elif key == "quick-terminal-screen":
                quick_terminal.enabled = True
                quick_terminal.screen = cls.QUICK_TERMINAL_SCREEN_MAP.get(
                    value.lower(), QuickTerminalScreen.MAIN
                )
            elif key == "quick-terminal-animation-duration":
                quick_terminal.enabled = True
                try:
                    # Ghostty uses fractional seconds, convert to milliseconds
                    quick_terminal.animation_duration = int(float(value) * 1000)
                except ValueError:
                    ctec.add_warning(
                        f"Invalid quick-terminal-animation-duration: {value}"
                    )

            # Store unrecognized settings as terminal-specific
            else:
                ctec.add_terminal_specific("ghostty", key, value)

        # Only add non-empty configs
        if any(
            getattr(scheme, f) is not None
            for f in [
                "foreground",
                "background",
                "cursor",
                "black",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
            ]
        ):
            ctec.color_scheme = scheme
        if font.family or font.size:
            ctec.font = font
        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor
        if window.columns or window.rows or window.opacity:
            ctec.window = window
        if behavior.shell or behavior.scrollback_lines:
            ctec.behavior = behavior
        if quick_terminal.enabled:
            ctec.quick_terminal = quick_terminal

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC to Ghostty configuration format."""
        lines = ["# Ghostty configuration", "# Generated by console-cowboy", ""]

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            lines.append("# Colors")
            if scheme.foreground:
                lines.append(f"foreground = {scheme.foreground.to_hex()}")
            if scheme.background:
                lines.append(f"background = {scheme.background.to_hex()}")
            if scheme.cursor:
                lines.append(f"cursor-color = {scheme.cursor.to_hex()}")
            if scheme.cursor_text:
                lines.append(f"cursor-text = {scheme.cursor_text.to_hex()}")
            if scheme.selection:
                lines.append(f"selection-background = {scheme.selection.to_hex()}")
            if scheme.selection_text:
                lines.append(f"selection-foreground = {scheme.selection_text.to_hex()}")

            # Export palette colors
            palette_colors = [
                ("black", 0),
                ("red", 1),
                ("green", 2),
                ("yellow", 3),
                ("blue", 4),
                ("magenta", 5),
                ("cyan", 6),
                ("white", 7),
                ("bright_black", 8),
                ("bright_red", 9),
                ("bright_green", 10),
                ("bright_yellow", 11),
                ("bright_blue", 12),
                ("bright_magenta", 13),
                ("bright_cyan", 14),
                ("bright_white", 15),
            ]
            for attr, idx in palette_colors:
                color = getattr(scheme, attr, None)
                if color:
                    lines.append(f"palette = {idx}={color.to_hex()}")
            lines.append("")

        # Export font settings
        if ctec.font:
            lines.append("# Font")
            if ctec.font.family:
                lines.append(f"font-family = {ctec.font.family}")
            if ctec.font.size:
                lines.append(f"font-size = {ctec.font.size}")
            if ctec.font.bold_font:
                lines.append(f"font-family-bold = {ctec.font.bold_font}")
            if ctec.font.italic_font:
                lines.append(f"font-family-italic = {ctec.font.italic_font}")
            if ctec.font.bold_italic_font:
                lines.append(f"font-family-bold-italic = {ctec.font.bold_italic_font}")
            if ctec.font.line_height and ctec.font.line_height != 1.0:
                adjust = int((ctec.font.line_height - 1.0) * 100)
                lines.append(f"adjust-cell-height = {adjust}")
            if ctec.font.cell_width and ctec.font.cell_width != 1.0:
                adjust = int((ctec.font.cell_width - 1.0) * 100)
                lines.append(f"adjust-cell-width = {adjust}")
            lines.append("")

        # Export cursor settings
        if ctec.cursor:
            lines.append("# Cursor")
            if ctec.cursor.style:
                style = cls.CURSOR_STYLE_REVERSE_MAP.get(ctec.cursor.style, "block")
                lines.append(f"cursor-style = {style}")
            if ctec.cursor.blink is not None:
                lines.append(f"cursor-style-blink = {str(ctec.cursor.blink).lower()}")
            lines.append("")

        # Export window settings
        if ctec.window:
            lines.append("# Window")
            if ctec.window.columns:
                lines.append(f"window-width = {ctec.window.columns}")
            if ctec.window.rows:
                lines.append(f"window-height = {ctec.window.rows}")
            if ctec.window.opacity is not None:
                lines.append(f"background-opacity = {ctec.window.opacity}")
            if ctec.window.blur:
                lines.append(f"background-blur-radius = {ctec.window.blur}")
            if ctec.window.padding_horizontal is not None:
                lines.append(f"window-padding-x = {ctec.window.padding_horizontal}")
            if ctec.window.padding_vertical is not None:
                lines.append(f"window-padding-y = {ctec.window.padding_vertical}")
            if ctec.window.decorations is not None:
                val = "true" if ctec.window.decorations else "none"
                lines.append(f"window-decoration = {val}")
            if ctec.window.startup_mode == "fullscreen":
                lines.append("fullscreen = true")
            if ctec.window.dynamic_title is not None:
                lines.append(
                    f"window-title-show-all = {str(ctec.window.dynamic_title).lower()}"
                )
            lines.append("")

        # Export behavior settings
        if ctec.behavior:
            lines.append("# Behavior")
            if ctec.behavior.shell:
                lines.append(f"command = {ctec.behavior.shell}")
            if ctec.behavior.working_directory:
                lines.append(f"working-directory = {ctec.behavior.working_directory}")
            if ctec.behavior.copy_on_select is not None:
                lines.append(
                    f"copy-on-select = {str(ctec.behavior.copy_on_select).lower()}"
                )
            if ctec.behavior.confirm_close is not None:
                lines.append(
                    f"confirm-close-surface = {str(ctec.behavior.confirm_close).lower()}"
                )
            lines.append("")

        # Export scroll settings (Ghostty uses bytes, not lines)
        if ctec.scroll:
            lines.append("# Scrollback")
            if ctec.scroll.disabled:
                lines.append("scrollback-limit = 0")
            else:
                # Convert to bytes - Ghostty default is 10MB (10485760 bytes)
                byte_count = ctec.scroll.get_effective_bytes(default_bytes=10485760)
                if byte_count > 0:
                    lines.append(f"scrollback-limit = {byte_count}")
            lines.append("")

        # Export quick terminal settings
        if ctec.quick_terminal and ctec.quick_terminal.enabled:
            lines.append("# Quick Terminal")
            if ctec.quick_terminal.position is not None:
                position = cls.QUICK_TERMINAL_POSITION_REVERSE_MAP.get(
                    ctec.quick_terminal.position, "top"
                )
                lines.append(f"quick-terminal-position = {position}")
            if ctec.quick_terminal.screen is not None:
                screen = cls.QUICK_TERMINAL_SCREEN_REVERSE_MAP.get(
                    ctec.quick_terminal.screen, "main"
                )
                lines.append(f"quick-terminal-screen = {screen}")
            if ctec.quick_terminal.animation_duration is not None:
                # Ghostty uses fractional seconds, convert from milliseconds
                duration_sec = ctec.quick_terminal.animation_duration / 1000.0
                lines.append(f"quick-terminal-animation-duration = {duration_sec}")
            lines.append("")

        # Restore terminal-specific settings
        ghostty_specific = ctec.get_terminal_specific("ghostty")
        if ghostty_specific:
            lines.append("# Terminal-specific settings")
            for setting in ghostty_specific:
                value = setting.value
                if isinstance(value, bool):
                    value = str(value).lower()
                lines.append(f"{setting.key} = {value}")
            lines.append("")

        # Handle text hints - Ghostty has limited support via link-url
        if ctec.text_hints and ctec.text_hints.rules:
            # Check if any rules look like URL patterns
            has_url_patterns = any(
                rule.hyperlinks or (rule.regex and "http" in rule.regex.lower())
                for rule in ctec.text_hints.rules
            )
            if has_url_patterns:
                # Ghostty's link-url enables basic URL detection by default
                lines.append("# URL detection (Ghostty has built-in URL matching)")
                lines.append("link-url = true")
                lines.append("")
            ctec.add_warning(
                f"Ghostty has limited text hint support. "
                f"{len(ctec.text_hints.rules)} custom rule(s) cannot be fully exported. "
                "Ghostty's built-in 'link-url' setting provides basic URL detection. "
                "Custom regex patterns via the 'link' config are planned but not yet available."
            )

        return "\n".join(lines)
