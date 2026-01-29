"""
Alacritty configuration adapter.

Alacritty uses YAML (versions < 0.13) or TOML (versions >= 0.13) format stored in
~/.config/alacritty/alacritty.yml or ~/.config/alacritty/alacritty.toml
"""

from pathlib import Path
from typing import Optional

import tomli
import tomli_w
import yaml

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    FontStyle,
    KeyBinding,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter


class AlacrittyAdapter(TerminalAdapter):
    """
    Adapter for Alacritty terminal emulator.

    Supports both YAML (legacy) and TOML (modern) configuration formats.
    """

    name = "alacritty"
    display_name = "Alacritty"
    description = "Cross-platform, GPU-accelerated terminal emulator"
    config_extensions = [".yml", ".yaml", ".toml"]
    default_config_paths = [
        ".config/alacritty/alacritty.toml",
        ".config/alacritty/alacritty.yml",
        ".alacritty.toml",
        ".alacritty.yml",
    ]

    CURSOR_STYLE_MAP = {
        "block": CursorStyle.BLOCK,
        "beam": CursorStyle.BEAM,
        "underline": CursorStyle.UNDERLINE,
    }

    CURSOR_STYLE_REVERSE_MAP = {v: k for k, v in CURSOR_STYLE_MAP.items()}

    @classmethod
    def _parse_color(cls, color_data: str | dict) -> Optional["Color"]:
        """Parse a color from Alacritty format."""
        if color_data is None:
            return None
        return normalize_color(color_data)

    @classmethod
    def _parse_colors(cls, colors: dict) -> ColorScheme:
        """Parse Alacritty colors section."""
        scheme = ColorScheme()

        if "primary" in colors:
            primary = colors["primary"]
            if "foreground" in primary:
                scheme.foreground = cls._parse_color(primary["foreground"])
            if "background" in primary:
                scheme.background = cls._parse_color(primary["background"])

        if "cursor" in colors:
            cursor = colors["cursor"]
            if "cursor" in cursor:
                scheme.cursor = cls._parse_color(cursor["cursor"])
            if "text" in cursor:
                scheme.cursor_text = cls._parse_color(cursor["text"])

        if "selection" in colors:
            selection = colors["selection"]
            if "background" in selection:
                scheme.selection = cls._parse_color(selection["background"])
            if "text" in selection:
                scheme.selection_text = cls._parse_color(selection["text"])

        if "normal" in colors:
            normal = colors["normal"]
            color_map = {
                "black": "black",
                "red": "red",
                "green": "green",
                "yellow": "yellow",
                "blue": "blue",
                "magenta": "magenta",
                "cyan": "cyan",
                "white": "white",
            }
            for alac_key, ctec_key in color_map.items():
                if alac_key in normal:
                    setattr(scheme, ctec_key, cls._parse_color(normal[alac_key]))

        if "bright" in colors:
            bright = colors["bright"]
            color_map = {
                "black": "bright_black",
                "red": "bright_red",
                "green": "bright_green",
                "yellow": "bright_yellow",
                "blue": "bright_blue",
                "magenta": "bright_magenta",
                "cyan": "bright_cyan",
                "white": "bright_white",
            }
            for alac_key, ctec_key in color_map.items():
                if alac_key in bright:
                    setattr(scheme, ctec_key, cls._parse_color(bright[alac_key]))

        return scheme

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse an Alacritty configuration file."""
        ctec = CTEC(source_terminal="alacritty")

        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()
            is_toml = path.suffix == ".toml"
        else:
            # Try to detect format
            is_toml = content.strip().startswith("[") or "=" in content.split("\n")[0]

        if is_toml:
            data = tomli.loads(content)
        else:
            data = yaml.safe_load(content) or {}

        # Parse colors
        if "colors" in data:
            ctec.color_scheme = cls._parse_colors(data["colors"])

        # Parse font
        if "font" in data:
            font_data = data["font"]
            font = FontConfig()
            if "normal" in font_data:
                normal = font_data["normal"]
                if "family" in normal:
                    font.family = normal["family"]
                # Parse font style from normal font
                if "style" in normal:
                    style_str = normal["style"].lower()
                    if "italic" in style_str:
                        font.style = FontStyle.ITALIC
                    elif "oblique" in style_str:
                        font.style = FontStyle.OBLIQUE
            if "bold" in font_data and "family" in font_data["bold"]:
                font.bold_font = font_data["bold"]["family"]
            if "italic" in font_data and "family" in font_data["italic"]:
                font.italic_font = font_data["italic"]["family"]
            if "bold_italic" in font_data and "family" in font_data["bold_italic"]:
                font.bold_italic_font = font_data["bold_italic"]["family"]
            if "size" in font_data:
                font.size = float(font_data["size"])
            if "offset" in font_data and "y" in font_data["offset"]:
                # Line height adjustment
                font.line_height = 1.0 + font_data["offset"]["y"] / 10
            ctec.font = font

        # Parse cursor
        if "cursor" in data:
            cursor_data = data["cursor"]
            cursor = CursorConfig()
            if "style" in cursor_data:
                style_data = cursor_data["style"]
                if isinstance(style_data, str):
                    cursor.style = cls.CURSOR_STYLE_MAP.get(
                        style_data.lower(), CursorStyle.BLOCK
                    )
                elif isinstance(style_data, dict) and "shape" in style_data:
                    cursor.style = cls.CURSOR_STYLE_MAP.get(
                        style_data["shape"].lower(), CursorStyle.BLOCK
                    )
                    if "blinking" in style_data:
                        cursor.blink = style_data["blinking"] not in (
                            "Off",
                            "Never",
                            False,
                        )
            if "blink_interval" in cursor_data:
                cursor.blink_interval = cursor_data["blink_interval"]
            ctec.cursor = cursor

        # Parse window
        if "window" in data:
            window_data = data["window"]
            window = WindowConfig()
            if "dimensions" in window_data:
                dims = window_data["dimensions"]
                if "columns" in dims:
                    window.columns = dims["columns"]
                if "lines" in dims:
                    window.rows = dims["lines"]
            if "opacity" in window_data:
                window.opacity = window_data["opacity"]
            if "blur" in window_data:
                blur_val = window_data["blur"]
                # Alacritty uses boolean blur; store as default radius if enabled
                if isinstance(blur_val, bool):
                    window.blur = 20 if blur_val else None
                elif isinstance(blur_val, int):
                    window.blur = blur_val if blur_val > 0 else None
            if "padding" in window_data:
                padding = window_data["padding"]
                if "x" in padding:
                    window.padding_horizontal = padding["x"]
                if "y" in padding:
                    window.padding_vertical = padding["y"]
            if "decorations" in window_data:
                window.decorations = window_data["decorations"] not in (
                    "None",
                    "none",
                    False,
                )
            if "startup_mode" in window_data:
                window.startup_mode = window_data["startup_mode"].lower()
            if "dynamic_title" in window_data:
                window.dynamic_title = window_data["dynamic_title"]
            ctec.window = window

        # Parse shell/behavior
        if "shell" in data:
            behavior = BehaviorConfig()
            shell_data = data["shell"]
            if isinstance(shell_data, str):
                behavior.shell = shell_data
            elif isinstance(shell_data, dict) and "program" in shell_data:
                behavior.shell = shell_data["program"]
            ctec.behavior = behavior

        if "scrolling" in data:
            scrolling = data["scrolling"]
            if "history" in scrolling:
                lines = scrolling["history"]
                # Alacritty max is 100,000 lines
                ctec.scroll = ScrollConfig.from_lines(lines)
            if "multiplier" in scrolling:
                if ctec.scroll is None:
                    ctec.scroll = ScrollConfig()
                ctec.scroll.multiplier = float(scrolling["multiplier"])

        if "bell" in data:
            if ctec.behavior is None:
                ctec.behavior = BehaviorConfig()
            bell_data = data["bell"]
            if "duration" in bell_data:
                if bell_data["duration"] == 0:
                    ctec.behavior.bell_mode = BellMode.NONE
                else:
                    ctec.behavior.bell_mode = BellMode.VISUAL

        if "mouse" in data:
            if ctec.behavior is None:
                ctec.behavior = BehaviorConfig()
            mouse_data = data["mouse"]
            # Alacritty doesn't have a single mouse enable toggle
            # but we can infer from hide_when_typing
            if "hide_when_typing" in mouse_data:
                ctec.add_terminal_specific(
                    "alacritty",
                    "mouse.hide_when_typing",
                    mouse_data["hide_when_typing"],
                )

        if "selection" in data:
            if ctec.behavior is None:
                ctec.behavior = BehaviorConfig()
            if "save_to_clipboard" in data["selection"]:
                ctec.behavior.copy_on_select = data["selection"]["save_to_clipboard"]

        # Parse key bindings
        if "keyboard" in data and "bindings" in data["keyboard"]:
            for binding in data["keyboard"]["bindings"]:
                if "key" in binding and "action" in binding:
                    kb = KeyBinding(
                        action=binding["action"],
                        key=binding["key"],
                        mods=binding.get("mods", "").split("+")
                        if binding.get("mods")
                        else [],
                    )
                    ctec.key_bindings.append(kb)
        # Legacy format
        elif "key_bindings" in data:
            for binding in data["key_bindings"]:
                if "key" in binding and "action" in binding:
                    kb = KeyBinding(
                        action=binding["action"],
                        key=binding["key"],
                        mods=binding.get("mods", "").split("|")
                        if binding.get("mods")
                        else [],
                    )
                    ctec.key_bindings.append(kb)

        # Store unrecognized top-level keys
        recognized_keys = {
            "colors",
            "font",
            "cursor",
            "window",
            "shell",
            "scrolling",
            "bell",
            "mouse",
            "selection",
            "keyboard",
            "key_bindings",
        }
        for key in data:
            if key not in recognized_keys:
                ctec.add_terminal_specific("alacritty", key, data[key])

        return ctec

    @classmethod
    def export(cls, ctec: CTEC, use_toml: bool = True) -> str:
        """
        Export CTEC to Alacritty configuration format.

        Args:
            ctec: CTEC configuration to export
            use_toml: If True, export as TOML; otherwise export as YAML

        Returns:
            Configuration string in the specified format
        """
        result = {}

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            colors = {}

            primary = {}
            if scheme.foreground:
                primary["foreground"] = scheme.foreground.to_hex()
            if scheme.background:
                primary["background"] = scheme.background.to_hex()
            if primary:
                colors["primary"] = primary

            cursor = {}
            if scheme.cursor:
                cursor["cursor"] = scheme.cursor.to_hex()
            if scheme.cursor_text:
                cursor["text"] = scheme.cursor_text.to_hex()
            if cursor:
                colors["cursor"] = cursor

            selection = {}
            if scheme.selection:
                selection["background"] = scheme.selection.to_hex()
            if scheme.selection_text:
                selection["text"] = scheme.selection_text.to_hex()
            if selection:
                colors["selection"] = selection

            normal = {}
            for ctec_key, alac_key in [
                ("black", "black"),
                ("red", "red"),
                ("green", "green"),
                ("yellow", "yellow"),
                ("blue", "blue"),
                ("magenta", "magenta"),
                ("cyan", "cyan"),
                ("white", "white"),
            ]:
                color = getattr(scheme, ctec_key, None)
                if color:
                    normal[alac_key] = color.to_hex()
            if normal:
                colors["normal"] = normal

            bright = {}
            for ctec_key, alac_key in [
                ("bright_black", "black"),
                ("bright_red", "red"),
                ("bright_green", "green"),
                ("bright_yellow", "yellow"),
                ("bright_blue", "blue"),
                ("bright_magenta", "magenta"),
                ("bright_cyan", "cyan"),
                ("bright_white", "white"),
            ]:
                color = getattr(scheme, ctec_key, None)
                if color:
                    bright[alac_key] = color.to_hex()
            if bright:
                colors["bright"] = bright

            if colors:
                result["colors"] = colors

        # Export font
        if ctec.font:
            font = {}
            if ctec.font.family:
                normal = {"family": ctec.font.family}
                # Add style if not default
                if ctec.font.style and ctec.font.style != FontStyle.NORMAL:
                    normal["style"] = ctec.font.style.value.capitalize()
                font["normal"] = normal
            if ctec.font.bold_font:
                font["bold"] = {"family": ctec.font.bold_font}
            if ctec.font.italic_font:
                font["italic"] = {"family": ctec.font.italic_font}
            if ctec.font.bold_italic_font:
                font["bold_italic"] = {"family": ctec.font.bold_italic_font}
            if ctec.font.size:
                font["size"] = ctec.font.size
            if ctec.font.line_height and ctec.font.line_height != 1.0:
                font["offset"] = {"y": int((ctec.font.line_height - 1.0) * 10)}
            if font:
                result["font"] = font

        # Export cursor
        if ctec.cursor:
            cursor = {}
            style = {}
            if ctec.cursor.style:
                style["shape"] = cls.CURSOR_STYLE_REVERSE_MAP.get(
                    ctec.cursor.style, "Block"
                ).capitalize()
            if ctec.cursor.blink is not None:
                style["blinking"] = "On" if ctec.cursor.blink else "Off"
            if style:
                cursor["style"] = style
            if ctec.cursor.blink_interval:
                cursor["blink_interval"] = ctec.cursor.blink_interval
            if cursor:
                result["cursor"] = cursor

        # Export window
        if ctec.window:
            window = {}
            if ctec.window.columns or ctec.window.rows:
                dims = {}
                if ctec.window.columns:
                    dims["columns"] = ctec.window.columns
                if ctec.window.rows:
                    dims["lines"] = ctec.window.rows
                window["dimensions"] = dims
            if ctec.window.opacity is not None:
                window["opacity"] = ctec.window.opacity
            if ctec.window.blur:
                # Alacritty uses boolean blur, not radius
                window["blur"] = True
            if (
                ctec.window.padding_horizontal is not None
                or ctec.window.padding_vertical is not None
            ):
                padding = {}
                if ctec.window.padding_horizontal is not None:
                    padding["x"] = ctec.window.padding_horizontal
                if ctec.window.padding_vertical is not None:
                    padding["y"] = ctec.window.padding_vertical
                window["padding"] = padding
            if ctec.window.decorations is not None:
                window["decorations"] = "Full" if ctec.window.decorations else "None"
            if ctec.window.startup_mode:
                window["startup_mode"] = ctec.window.startup_mode.capitalize()
            if ctec.window.dynamic_title is not None:
                window["dynamic_title"] = ctec.window.dynamic_title
            if window:
                result["window"] = window

        # Export behavior
        if ctec.behavior:
            if ctec.behavior.shell:
                result["shell"] = {"program": ctec.behavior.shell}
            if ctec.behavior.bell_mode is not None:
                if ctec.behavior.bell_mode == BellMode.NONE:
                    result["bell"] = {"duration": 0}
                else:
                    result["bell"] = {"duration": 100}
            if ctec.behavior.copy_on_select is not None:
                result["selection"] = {
                    "save_to_clipboard": ctec.behavior.copy_on_select
                }

        # Export scroll settings (Alacritty max is 100,000 lines)
        if ctec.scroll:
            scrolling = {}
            # Alacritty uses line-based scrollback with max 100,000
            lines = ctec.scroll.get_effective_lines(default=10000, max_lines=100000)
            if (
                ctec.scroll.disabled
                or ctec.scroll.lines is not None
                or ctec.scroll.unlimited
            ):
                scrolling["history"] = lines
            if ctec.scroll.multiplier is not None:
                scrolling["multiplier"] = int(ctec.scroll.multiplier)
            if scrolling:
                result["scrolling"] = scrolling

        # Export key bindings
        if ctec.key_bindings:
            bindings = []
            for kb in ctec.key_bindings:
                binding = {"key": kb.key, "action": kb.action}
                if kb.mods:
                    binding["mods"] = "+".join(kb.mods)
                bindings.append(binding)
            result["keyboard"] = {"bindings": bindings}

        # Restore terminal-specific settings
        for setting in ctec.get_terminal_specific("alacritty"):
            result[setting.key] = setting.value

        if use_toml:
            return tomli_w.dumps(result)
        else:
            return yaml.dump(result, default_flow_style=False, sort_keys=False)
