"""
Wezterm configuration adapter.

Wezterm uses Lua for configuration, stored in ~/.wezterm.lua or
~/.config/wezterm/wezterm.lua

This adapter generates and parses a simplified subset of Wezterm's
Lua configuration format.
"""

import re
from pathlib import Path
from typing import Optional

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    FontWeight,
    KeyBinding,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color
from console_cowboy.utils.fonts import is_postscript_name, postscript_to_friendly

from .base import TerminalAdapter


class WeztermAdapter(TerminalAdapter):
    """
    Adapter for Wezterm terminal emulator.

    Wezterm uses Lua configuration which is complex to fully parse.
    This adapter handles common configuration patterns and provides
    best-effort parsing of Lua configs.
    """

    name = "wezterm"
    display_name = "Wezterm"
    description = "GPU-accelerated terminal emulator with Lua configuration"
    config_extensions = [".lua"]
    default_config_paths = [
        ".wezterm.lua",
        ".config/wezterm/wezterm.lua",
    ]

    CURSOR_STYLE_MAP = {
        "SteadyBlock": CursorStyle.BLOCK,
        "BlinkingBlock": CursorStyle.BLOCK,
        "SteadyBar": CursorStyle.BEAM,
        "BlinkingBar": CursorStyle.BEAM,
        "SteadyUnderline": CursorStyle.UNDERLINE,
        "BlinkingUnderline": CursorStyle.UNDERLINE,
    }

    @classmethod
    def _extract_lua_value(cls, content: str, key: str) -> str | None:
        """Extract a simple value from Lua config (config.key = value).

        Handles nested braces for function calls like wezterm.font_with_fallback({...}).
        """
        # First, find the start of the assignment
        pattern = rf"config\.{re.escape(key)}\s*="
        match = re.search(pattern, content)
        if not match:
            return None

        start = match.end()

        # Skip whitespace
        while start < len(content) and content[start] in " \t":
            start += 1

        # If the value starts with wezterm. (a function call), extract until balanced parens
        if content[start:].startswith("wezterm."):
            # Find opening paren
            paren_start = content.find("(", start)
            if paren_start == -1:
                # No paren, extract until newline
                end = content.find("\n", start)
                return (
                    content[start:end].strip() if end != -1 else content[start:].strip()
                )

            # Find matching closing paren, accounting for nested parens and braces
            depth_paren = 0
            depth_brace = 0
            i = paren_start
            while i < len(content):
                c = content[i]
                if c == "(":
                    depth_paren += 1
                elif c == ")":
                    depth_paren -= 1
                    if depth_paren == 0:
                        return content[start : i + 1].strip()
                elif c == "{":
                    depth_brace += 1
                elif c == "}":
                    depth_brace -= 1
                i += 1
            # Didn't find matching paren
            return None

        # Otherwise, extract simple value until newline or comma
        end = start
        while end < len(content) and content[end] not in "\n,":
            end += 1

        value = content[start:end].strip()
        # Remove quotes if present
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        return value

    @classmethod
    def _extract_lua_table(cls, content: str, key: str) -> str | None:
        """Extract a table value from Lua config."""
        # Match patterns like: config.colors = { ... }
        pattern = rf"config\.{re.escape(key)}\s*=\s*\{{"
        match = re.search(pattern, content)
        if match:
            start = match.end() - 1
            depth = 0
            for i, char in enumerate(content[start:]):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return content[start : start + i + 1]
        return None

    @classmethod
    def _parse_lua_color(cls, color_str: str) -> Optional["Color"]:
        """Parse a color from Lua format."""
        color_str = color_str.strip().strip("'\"")
        if color_str.lower() == "none":
            return None
        try:
            return normalize_color(color_str)
        except ValueError:
            return None

    @classmethod
    def _parse_colors_table(cls, table_str: str) -> ColorScheme:
        """Parse a Wezterm colors table."""
        scheme = ColorScheme()

        # Parse simple color assignments
        color_patterns = {
            "foreground": "foreground",
            "background": "background",
            "cursor_fg": "cursor_text",
            "cursor_bg": "cursor",
            "selection_fg": "selection_text",
            "selection_bg": "selection",
        }

        for wez_key, ctec_key in color_patterns.items():
            pattern = rf'{wez_key}\s*=\s*["\']([^"\']+)["\']'
            match = re.search(pattern, table_str)
            if match:
                color = cls._parse_lua_color(match.group(1))
                if color:
                    setattr(scheme, ctec_key, color)

        # Parse ansi colors array
        ansi_pattern = r"ansi\s*=\s*\{([^}]+)\}"
        ansi_match = re.search(ansi_pattern, table_str)
        if ansi_match:
            colors_str = ansi_match.group(1)
            colors = re.findall(r'["\']([^"\']+)["\']', colors_str)
            ansi_names = [
                "black",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
            ]
            for name, color_str in zip(ansi_names, colors, strict=False):
                color = cls._parse_lua_color(color_str)
                if color:
                    setattr(scheme, name, color)

        # Parse bright/brights colors array
        brights_pattern = r"brights\s*=\s*\{([^}]+)\}"
        brights_match = re.search(brights_pattern, table_str)
        if brights_match:
            colors_str = brights_match.group(1)
            colors = re.findall(r'["\']([^"\']+)["\']', colors_str)
            bright_names = [
                "bright_black",
                "bright_red",
                "bright_green",
                "bright_yellow",
                "bright_blue",
                "bright_magenta",
                "bright_cyan",
                "bright_white",
            ]
            for name, color_str in zip(bright_names, colors, strict=False):
                color = cls._parse_lua_color(color_str)
                if color:
                    setattr(scheme, name, color)

        return scheme

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse a Wezterm configuration file."""
        ctec = CTEC(source_terminal="wezterm")

        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()

        ctec.add_warning(
            "Wezterm uses Lua configuration. Some settings may not be fully parsed."
        )

        # Parse colors
        colors_table = cls._extract_lua_table(content, "colors")
        if colors_table:
            ctec.color_scheme = cls._parse_colors_table(colors_table)

        # Parse font
        font = FontConfig()
        font_family = cls._extract_lua_value(content, "font")
        if font_family:
            # Check for wezterm.font_with_fallback first
            fallback_match = re.search(
                r"wezterm\.font_with_fallback\s*\(\s*\{(.+?)\}\s*\)",
                font_family,
                re.DOTALL,
            )
            if fallback_match:
                # Parse fallback fonts list - handles both table and string entries
                fonts_str = fallback_match.group(1)

                # Check for table entry with weight: { family = "Name", weight = "Bold" }
                table_match = re.search(
                    r'\{\s*family\s*=\s*["\']([^"\']+)["\']\s*,\s*weight\s*=\s*["\']?(\w+)["\']?\s*\}',
                    fonts_str,
                )
                if table_match:
                    font.family = table_match.group(1)
                    try:
                        font.weight = FontWeight.from_string(table_match.group(2))
                    except (ValueError, KeyError):
                        ctec.add_warning(f"Unknown font weight: {table_match.group(2)}")
                    # Get remaining fallback fonts (simple strings)
                    remaining = fonts_str[table_match.end() :]
                    fallbacks = re.findall(r'["\']([^"\']+)["\']', remaining)
                    if fallbacks:
                        font.fallback_fonts = fallbacks
                else:
                    # Simple string entries
                    font_entries = re.findall(r'["\']([^"\']+)["\']', fonts_str)
                    if font_entries:
                        font.family = font_entries[0]
                        if len(font_entries) > 1:
                            font.fallback_fonts = font_entries[1:]
            else:
                # Extract font family from wezterm.font("Family", {options})
                family_match = re.search(
                    r'wezterm\.font\s*\(\s*["\']([^"\']+)["\']', font_family
                )
                if family_match:
                    font.family = family_match.group(1)
                    # Check for weight parameter
                    weight_match = re.search(
                        r'weight\s*=\s*["\']?(\w+)["\']?', font_family
                    )
                    if weight_match:
                        weight_str = weight_match.group(1)
                        try:
                            font.weight = FontWeight.from_string(weight_str)
                        except (ValueError, KeyError):
                            ctec.add_warning(f"Unknown font weight: {weight_str}")

        font_size = cls._extract_lua_value(content, "font_size")
        if font_size:
            try:
                font.size = float(font_size)
            except ValueError:
                ctec.add_warning(f"Invalid font_size: {font_size}")

        line_height = cls._extract_lua_value(content, "line_height")
        if line_height:
            try:
                font.line_height = float(line_height)
            except ValueError:
                ctec.add_warning(f"Invalid line_height: {line_height}")

        if font.family or font.size:
            ctec.font = font

        # Parse cursor
        cursor = CursorConfig()
        cursor_style = cls._extract_lua_value(content, "default_cursor_style")
        if cursor_style:
            cursor_style = cursor_style.strip("'\"")
            if cursor_style in cls.CURSOR_STYLE_MAP:
                cursor.style = cls.CURSOR_STYLE_MAP[cursor_style]
                cursor.blink = "Blinking" in cursor_style

        cursor_blink = cls._extract_lua_value(content, "cursor_blink_rate")
        if cursor_blink:
            try:
                rate = int(cursor_blink)
                cursor.blink = rate > 0
                if rate > 0:
                    cursor.blink_interval = rate
            except ValueError:
                pass

        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor

        # Parse window
        window = WindowConfig()

        # Initial cols/rows
        initial_cols = cls._extract_lua_value(content, "initial_cols")
        if initial_cols:
            try:
                window.columns = int(initial_cols)
            except ValueError:
                pass

        initial_rows = cls._extract_lua_value(content, "initial_rows")
        if initial_rows:
            try:
                window.rows = int(initial_rows)
            except ValueError:
                pass

        # Window opacity
        opacity = cls._extract_lua_value(content, "window_background_opacity")
        if opacity:
            try:
                window.opacity = float(opacity)
            except ValueError:
                pass

        # Window blur (macOS only)
        blur = cls._extract_lua_value(content, "macos_window_background_blur")
        if blur:
            try:
                window.blur = int(blur)
            except ValueError:
                pass

        # Window padding
        padding_table = cls._extract_lua_table(content, "window_padding")
        if padding_table:
            left_match = re.search(r"left\s*=\s*(\d+)", padding_table)
            top_match = re.search(r"top\s*=\s*(\d+)", padding_table)
            if left_match:
                window.padding_horizontal = int(left_match.group(1))
            if top_match:
                window.padding_vertical = int(top_match.group(1))

        # Window decorations
        decorations = cls._extract_lua_value(content, "window_decorations")
        if decorations:
            decorations = decorations.strip("'\"")
            window.decorations = decorations.upper() not in ("NONE", "RESIZE")

        if (
            window.columns
            or window.rows
            or window.opacity is not None
            or window.blur is not None
        ):
            ctec.window = window

        # Parse behavior
        behavior = BehaviorConfig()

        # Default program/shell
        default_prog = cls._extract_lua_value(content, "default_prog")
        if default_prog:
            # Extract from array like { '/bin/bash' }
            prog_match = re.search(r'["\']([^"\']+)["\']', default_prog)
            if prog_match:
                behavior.shell = prog_match.group(1)

        scrollback = cls._extract_lua_value(content, "scrollback_lines")
        if scrollback:
            try:
                lines = int(scrollback)
                ctec.scroll = ScrollConfig.from_lines(lines)
            except ValueError:
                ctec.add_warning(f"Invalid scrollback_lines: {scrollback}")

        # Bell
        audible_bell = cls._extract_lua_value(content, "audible_bell")
        if audible_bell:
            audible_bell = audible_bell.strip("'\"")
            if audible_bell == "Disabled":
                behavior.bell_mode = BellMode.NONE
            else:
                behavior.bell_mode = BellMode.AUDIBLE

        visual_bell = cls._extract_lua_table(content, "visual_bell")
        if visual_bell and "duration_ms" in visual_bell:
            duration_match = re.search(r"duration_ms\s*=\s*(\d+)", visual_bell)
            if duration_match and int(duration_match.group(1)) > 0:
                behavior.bell_mode = BellMode.VISUAL

        if behavior.shell or behavior.scrollback_lines or behavior.bell_mode:
            ctec.behavior = behavior

        # Parse key bindings
        keys_table = cls._extract_lua_table(content, "keys")
        if keys_table:
            # Match patterns like { key = "v", mods = "CTRL", action = ... }
            binding_pattern = r'\{\s*key\s*=\s*["\']([^"\']+)["\']\s*,\s*mods\s*=\s*["\']([^"\']+)["\']\s*,\s*action\s*=\s*([^}]+)\}'
            for match in re.finditer(binding_pattern, keys_table):
                key = match.group(1)
                mods = match.group(2).split("|")
                action = match.group(3).strip()
                # Simplify action for storage
                action_match = re.search(r"act\.(\w+)", action)
                if action_match:
                    action = action_match.group(1)
                ctec.key_bindings.append(KeyBinding(action=action, key=key, mods=mods))

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC to Wezterm Lua configuration format."""
        lines = [
            "-- Wezterm configuration",
            "-- Generated by console-cowboy",
            "",
            "local wezterm = require 'wezterm'",
            "local config = wezterm.config_builder()",
            "",
        ]

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            lines.append("-- Colors")
            lines.append("config.colors = {")

            if scheme.foreground:
                lines.append(f'  foreground = "{scheme.foreground.to_hex()}",')
            if scheme.background:
                lines.append(f'  background = "{scheme.background.to_hex()}",')
            if scheme.cursor:
                lines.append(f'  cursor_bg = "{scheme.cursor.to_hex()}",')
            if scheme.cursor_text:
                lines.append(f'  cursor_fg = "{scheme.cursor_text.to_hex()}",')
            if scheme.selection:
                lines.append(f'  selection_bg = "{scheme.selection.to_hex()}",')
            if scheme.selection_text:
                lines.append(f'  selection_fg = "{scheme.selection_text.to_hex()}",')

            # ANSI colors
            ansi_colors = []
            for attr in [
                "black",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
            ]:
                color = getattr(scheme, attr, None)
                if color:
                    ansi_colors.append(f'"{color.to_hex()}"')
            if ansi_colors:
                lines.append(f"  ansi = {{ {', '.join(ansi_colors)} }},")

            # Bright colors
            bright_colors = []
            for attr in [
                "bright_black",
                "bright_red",
                "bright_green",
                "bright_yellow",
                "bright_blue",
                "bright_magenta",
                "bright_cyan",
                "bright_white",
            ]:
                color = getattr(scheme, attr, None)
                if color:
                    bright_colors.append(f'"{color.to_hex()}"')
            if bright_colors:
                lines.append(f"  brights = {{ {', '.join(bright_colors)} }},")

            lines.append("}")
            lines.append("")

        # Export font
        if ctec.font:
            lines.append("-- Font")
            if ctec.font.family:
                font_family = ctec.font.family
                # Convert PostScript names to friendly names for Wezterm
                if is_postscript_name(font_family):
                    font_family = postscript_to_friendly(font_family)

                # Determine if we need fallback fonts
                if ctec.font.fallback_fonts:
                    # WezTerm supports weight in font_with_fallback via table syntax
                    if ctec.font.weight:
                        weight_name = ctec.font.weight.to_string()
                        primary = (
                            f'{{ family = "{font_family}", weight = "{weight_name}" }}'
                        )
                    else:
                        primary = f'"{font_family}"'
                    fallbacks_str = ", ".join(
                        f'"{f}"' for f in ctec.font.fallback_fonts
                    )
                    lines.append(
                        f"config.font = wezterm.font_with_fallback({{ {primary}, {fallbacks_str} }})"
                    )
                elif ctec.font.weight:
                    # Use font with weight parameter
                    weight_name = ctec.font.weight.to_string()
                    lines.append(
                        f'config.font = wezterm.font("{font_family}", {{weight="{weight_name}"}})'
                    )
                else:
                    lines.append(f'config.font = wezterm.font("{font_family}")')
            if ctec.font.size:
                lines.append(f"config.font_size = {ctec.font.size}")
            if ctec.font.line_height:
                lines.append(f"config.line_height = {ctec.font.line_height}")
            lines.append("")

        # Export cursor
        if ctec.cursor:
            lines.append("-- Cursor")
            if ctec.cursor.style:
                style_map = {
                    CursorStyle.BLOCK: ("SteadyBlock", "BlinkingBlock"),
                    CursorStyle.BEAM: ("SteadyBar", "BlinkingBar"),
                    CursorStyle.UNDERLINE: ("SteadyUnderline", "BlinkingUnderline"),
                }
                styles = style_map.get(
                    ctec.cursor.style, ("SteadyBlock", "BlinkingBlock")
                )
                style = styles[1] if ctec.cursor.blink else styles[0]
                lines.append(f'config.default_cursor_style = "{style}"')
            if ctec.cursor.blink_interval:
                lines.append(f"config.cursor_blink_rate = {ctec.cursor.blink_interval}")
            lines.append("")

        # Export window
        if ctec.window:
            lines.append("-- Window")
            if ctec.window.columns:
                lines.append(f"config.initial_cols = {ctec.window.columns}")
            if ctec.window.rows:
                lines.append(f"config.initial_rows = {ctec.window.rows}")
            if ctec.window.opacity is not None:
                lines.append(
                    f"config.window_background_opacity = {ctec.window.opacity}"
                )
            if ctec.window.blur is not None:
                lines.append(
                    f"config.macos_window_background_blur = {ctec.window.blur}"
                )
            if (
                ctec.window.padding_horizontal is not None
                or ctec.window.padding_vertical is not None
            ):
                h = ctec.window.padding_horizontal or 0
                v = ctec.window.padding_vertical or 0
                lines.append("config.window_padding = {")
                lines.append(f"  left = {h},")
                lines.append(f"  right = {h},")
                lines.append(f"  top = {v},")
                lines.append(f"  bottom = {v},")
                lines.append("}")
            if ctec.window.decorations is not None:
                val = "FULL" if ctec.window.decorations else "NONE"
                lines.append(f'config.window_decorations = "{val}"')
            lines.append("")

        # Export behavior
        if ctec.behavior:
            lines.append("-- Behavior")
            if ctec.behavior.shell:
                lines.append(f'config.default_prog = {{ "{ctec.behavior.shell}" }}')
            if ctec.behavior.bell_mode is not None:
                if ctec.behavior.bell_mode == BellMode.NONE:
                    lines.append('config.audible_bell = "Disabled"')
                elif ctec.behavior.bell_mode == BellMode.VISUAL:
                    lines.append('config.audible_bell = "Disabled"')
                    lines.append("config.visual_bell = {")
                    lines.append('  fade_in_function = "EaseIn",')
                    lines.append("  fade_in_duration_ms = 50,")
                    lines.append('  fade_out_function = "EaseOut",')
                    lines.append("  fade_out_duration_ms = 50,")
                    lines.append("}")
                else:
                    lines.append('config.audible_bell = "SystemBeep"')
            lines.append("")

        # Export scroll settings (Wezterm default is 3500 lines)
        if ctec.scroll:
            lines.append("-- Scrollback")
            # Wezterm doesn't have explicit unlimited mode, use large value
            scroll_lines = ctec.scroll.get_effective_lines(
                default=3500, max_lines=1000000
            )
            if (
                ctec.scroll.disabled
                or ctec.scroll.lines is not None
                or ctec.scroll.unlimited
            ):
                lines.append(f"config.scrollback_lines = {scroll_lines}")
            lines.append("")

        # Export key bindings
        if ctec.key_bindings:
            lines.append("-- Key bindings")
            lines.append("config.keys = {")
            for kb in ctec.key_bindings:
                mods = "|".join(kb.mods) if kb.mods else "NONE"
                lines.append(
                    f'  {{ key = "{kb.key}", mods = "{mods}", action = wezterm.action.{kb.action} }},'
                )
            lines.append("}")
            lines.append("")

        # Restore terminal-specific settings
        wezterm_specific = ctec.get_terminal_specific("wezterm")
        if wezterm_specific:
            lines.append("-- Terminal-specific settings")
            for setting in wezterm_specific:
                value = setting.value
                if isinstance(value, str):
                    value = f'"{value}"'
                elif isinstance(value, bool):
                    value = str(value).lower()
                lines.append(f"config.{setting.key} = {value}")
            lines.append("")

        lines.append("return config")
        return "\n".join(lines)
