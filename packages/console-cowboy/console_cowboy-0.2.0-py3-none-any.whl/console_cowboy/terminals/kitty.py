"""
Kitty configuration adapter.

Kitty uses a simple key-value configuration format stored in
~/.config/kitty/kitty.conf
"""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    KeyBinding,
    QuickTerminalConfig,
    QuickTerminalPosition,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter


class KittyAdapter(TerminalAdapter):
    """
    Adapter for Kitty terminal emulator.

    Kitty uses a simple key-value configuration format with support
    for comments (lines starting with #) and includes.
    """

    name = "kitty"
    display_name = "Kitty"
    description = "Cross-platform, GPU-based terminal emulator"
    config_extensions = [".conf"]
    default_config_paths = [
        ".config/kitty/kitty.conf",
    ]

    CURSOR_STYLE_MAP = {
        "block": CursorStyle.BLOCK,
        "beam": CursorStyle.BEAM,
        "underline": CursorStyle.UNDERLINE,
    }

    CURSOR_STYLE_REVERSE_MAP = {v: k for k, v in CURSOR_STYLE_MAP.items()}

    # Kitty color key mappings
    COLOR_KEY_MAP = {
        "foreground": "foreground",
        "background": "background",
        "cursor": "cursor",
        "cursor_text_color": "cursor_text",
        "selection_foreground": "selection_text",
        "selection_background": "selection",
        "color0": "black",
        "color1": "red",
        "color2": "green",
        "color3": "yellow",
        "color4": "blue",
        "color5": "magenta",
        "color6": "cyan",
        "color7": "white",
        "color8": "bright_black",
        "color9": "bright_red",
        "color10": "bright_green",
        "color11": "bright_yellow",
        "color12": "bright_blue",
        "color13": "bright_magenta",
        "color14": "bright_cyan",
        "color15": "bright_white",
    }

    COLOR_KEY_REVERSE_MAP = {v: k for k, v in COLOR_KEY_MAP.items()}

    # Kitty quick-access-terminal edge mapping (kitten feature in 0.42+)
    # The quick-access-terminal kitten uses a separate config file but we support
    # parsing/exporting these settings for cross-terminal compatibility
    QUICK_TERMINAL_EDGE_MAP = {
        "top": QuickTerminalPosition.TOP,
        "bottom": QuickTerminalPosition.BOTTOM,
        "left": QuickTerminalPosition.LEFT,
        "right": QuickTerminalPosition.RIGHT,
        "background": QuickTerminalPosition.BACKGROUND,
    }

    QUICK_TERMINAL_EDGE_REVERSE_MAP = {v: k for k, v in QUICK_TERMINAL_EDGE_MAP.items()}

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse a Kitty configuration file."""
        ctec = CTEC(source_terminal="kitty")
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

            # Split on first whitespace
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue

            key, value = parts[0], parts[1]

            # Parse color settings
            if key in cls.COLOR_KEY_MAP:
                ctec_key = cls.COLOR_KEY_MAP[key]
                try:
                    color = normalize_color(value)
                    setattr(scheme, ctec_key, color)
                except ValueError:
                    ctec.add_warning(f"Invalid color value for {key}: {value}")

            # Parse font settings
            elif key == "font_family":
                font.family = value
            elif key == "font_size":
                try:
                    font.size = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid font_size: {value}")
            elif key == "bold_font":
                if value.lower() != "auto":
                    font.bold_font = value
            elif key == "italic_font":
                if value.lower() != "auto":
                    font.italic_font = value
            elif key == "bold_italic_font":
                if value.lower() != "auto":
                    font.bold_italic_font = value
            elif key == "adjust_line_height":
                try:
                    # Can be percentage (e.g., "110%") or absolute
                    if value.endswith("%"):
                        font.line_height = float(value[:-1]) / 100
                    else:
                        font.line_height = 1.0 + float(value) / 10
                except ValueError:
                    ctec.add_warning(f"Invalid adjust_line_height: {value}")
            elif key == "disable_ligatures":
                font.ligatures = value.lower() == "never"
            elif key == "symbol_map":
                # Format: U+E0A0-U+E0A3,U+E0B0-U+E0B3 Symbols Nerd Font
                # Parse unicode range and font name
                parts = value.split(None, 1)
                if len(parts) == 2:
                    unicode_range, font_name = parts
                    if font.symbol_map is None:
                        font.symbol_map = {}
                    font.symbol_map[unicode_range] = font_name
            elif key == "box_drawing_scale":
                try:
                    # Kitty uses 4 values, we store just the first as a representative
                    parts = value.split(",")
                    if parts:
                        font.box_drawing_scale = float(parts[0].strip())
                except ValueError:
                    ctec.add_warning(f"Invalid box_drawing_scale: {value}")

            # Parse cursor settings
            elif key == "cursor_shape":
                cursor.style = cls.CURSOR_STYLE_MAP.get(
                    value.lower(), CursorStyle.BLOCK
                )
            elif key == "cursor_blink_interval":
                try:
                    interval = float(value)
                    cursor.blink = interval > 0
                    if interval > 0:
                        cursor.blink_interval = int(interval * 1000)  # Convert to ms
                except ValueError:
                    ctec.add_warning(f"Invalid cursor_blink_interval: {value}")

            # Parse window settings
            elif key == "initial_window_width":
                try:
                    # Can be "80c" for columns or pixels
                    if value.endswith("c"):
                        window.columns = int(value[:-1])
                    else:
                        ctec.add_terminal_specific("kitty", key, int(value))
                except ValueError:
                    ctec.add_warning(f"Invalid initial_window_width: {value}")
            elif key == "initial_window_height":
                try:
                    if value.endswith("c"):
                        window.rows = int(value[:-1])
                    else:
                        ctec.add_terminal_specific("kitty", key, int(value))
                except ValueError:
                    ctec.add_warning(f"Invalid initial_window_height: {value}")
            elif key == "background_opacity":
                try:
                    window.opacity = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid background_opacity: {value}")
            elif key == "background_blur":
                try:
                    window.blur = int(value)
                except ValueError:
                    ctec.add_warning(f"Invalid background_blur: {value}")
            elif key == "window_padding_width":
                try:
                    # Kitty uses single value for all sides
                    padding = int(value)
                    window.padding_horizontal = padding
                    window.padding_vertical = padding
                except ValueError:
                    ctec.add_warning(f"Invalid window_padding_width: {value}")
            elif key == "hide_window_decorations":
                window.decorations = value.lower() == "no"
            elif key == "remember_window_size":
                ctec.add_terminal_specific("kitty", key, value.lower() == "yes")
            elif key == "dynamic_title":
                window.dynamic_title = value.lower() == "yes"

            # Parse behavior settings
            elif key == "shell":
                if value != ".":
                    behavior.shell = value
            elif key == "scrollback_lines":
                try:
                    lines = int(value)
                    # Kitty uses -1 for unlimited, 0 for disabled
                    ctec.scroll = ScrollConfig.from_lines(lines)
                except ValueError:
                    ctec.add_warning(f"Invalid scrollback_lines: {value}")
            elif key == "wheel_scroll_multiplier":
                try:
                    if ctec.scroll is None:
                        ctec.scroll = ScrollConfig()
                    ctec.scroll.multiplier = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid wheel_scroll_multiplier: {value}")
            elif key == "enable_audio_bell":
                if value.lower() == "no":
                    behavior.bell_mode = BellMode.NONE
                else:
                    behavior.bell_mode = BellMode.AUDIBLE
            elif key == "visual_bell_duration":
                try:
                    if float(value) > 0:
                        behavior.bell_mode = BellMode.VISUAL
                except ValueError:
                    ctec.add_warning(f"Invalid visual_bell_duration: {value}")
            elif key == "copy_on_select":
                behavior.copy_on_select = value.lower() == "yes"
            elif key == "confirm_os_window_close":
                try:
                    behavior.confirm_close = int(value) > 0
                except ValueError:
                    behavior.confirm_close = value.lower() == "yes"
            elif key == "close_on_child_death":
                behavior.close_on_exit = "close" if value.lower() == "yes" else "hold"
            elif key == "mouse_hide_wait":
                try:
                    behavior.mouse_enabled = float(value) >= 0
                except ValueError:
                    ctec.add_warning(f"Invalid mouse_hide_wait: {value}")

            # Parse key bindings
            elif key == "map":
                # Format: map <keys> <action>
                binding_parts = value.split(None, 1)
                if len(binding_parts) >= 2:
                    keys, action = binding_parts
                    # Parse modifier+key format
                    key_parts = keys.split("+")
                    if len(key_parts) > 1:
                        mods = key_parts[:-1]
                        actual_key = key_parts[-1]
                    else:
                        mods = []
                        actual_key = keys
                    ctec.key_bindings.append(
                        KeyBinding(action=action, key=actual_key, mods=mods)
                    )

            # Parse quick-access-terminal kitten settings (Kitty 0.42+)
            # These are typically in quick-access-terminal.conf but we support
            # them in main config for cross-terminal compatibility
            elif key == "edge":
                quick_terminal.enabled = True
                quick_terminal.position = cls.QUICK_TERMINAL_EDGE_MAP.get(
                    value.lower(), QuickTerminalPosition.TOP
                )
            elif key == "hide_on_focus_loss":
                quick_terminal.enabled = True
                quick_terminal.hide_on_focus_loss = value.lower() == "yes"
            # Note: background_opacity in quick terminal context overrides
            # the main window opacity for the quick terminal window only

            # Store unrecognized settings
            else:
                ctec.add_terminal_specific("kitty", key, value)

        # Only add non-empty configs
        if any(
            getattr(scheme, f) is not None
            for f in ["foreground", "background", "black"]
        ):
            ctec.color_scheme = scheme
        if font.family or font.size or font.symbol_map or font.ligatures is not None:
            ctec.font = font
        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor
        if window.columns or window.rows or window.opacity:
            ctec.window = window
        if behavior.shell or behavior.scrollback_lines or behavior.bell_mode:
            ctec.behavior = behavior
        if quick_terminal.enabled:
            ctec.quick_terminal = quick_terminal

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC to Kitty configuration format."""
        lines = ["# Kitty configuration", "# Generated by console-cowboy", ""]

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            lines.append("# Colors")
            for ctec_key, kitty_key in cls.COLOR_KEY_REVERSE_MAP.items():
                color = getattr(scheme, ctec_key, None)
                if color:
                    lines.append(f"{kitty_key} {color.to_hex()}")
            lines.append("")

        # Export font settings
        if ctec.font:
            lines.append("# Font")
            if ctec.font.family:
                lines.append(f"font_family {ctec.font.family}")
            if ctec.font.size:
                lines.append(f"font_size {ctec.font.size}")
            if ctec.font.bold_font:
                lines.append(f"bold_font {ctec.font.bold_font}")
            if ctec.font.italic_font:
                lines.append(f"italic_font {ctec.font.italic_font}")
            if ctec.font.bold_italic_font:
                lines.append(f"bold_italic_font {ctec.font.bold_italic_font}")
            if ctec.font.line_height and ctec.font.line_height != 1.0:
                lines.append(f"adjust_line_height {int(ctec.font.line_height * 100)}%")
            if ctec.font.ligatures is not None:
                # disable_ligatures=never means ligatures are ON
                # disable_ligatures=always means ligatures are OFF
                val = "never" if ctec.font.ligatures else "always"
                lines.append(f"disable_ligatures {val}")
            if ctec.font.symbol_map:
                for unicode_range, font_name in ctec.font.symbol_map.items():
                    lines.append(f"symbol_map {unicode_range} {font_name}")
            if ctec.font.box_drawing_scale is not None:
                # Kitty expects 4 values, use the same value for all
                scale = ctec.font.box_drawing_scale
                lines.append(f"box_drawing_scale {scale}, {scale}, {scale}, {scale}")
            lines.append("")

        # Export cursor settings
        if ctec.cursor:
            lines.append("# Cursor")
            if ctec.cursor.style:
                style = cls.CURSOR_STYLE_REVERSE_MAP.get(ctec.cursor.style, "block")
                lines.append(f"cursor_shape {style}")
            if ctec.cursor.blink is not None:
                if ctec.cursor.blink:
                    interval = (ctec.cursor.blink_interval or 500) / 1000.0
                    lines.append(f"cursor_blink_interval {interval}")
                else:
                    lines.append("cursor_blink_interval 0")
            lines.append("")

        # Export window settings
        if ctec.window:
            lines.append("# Window")
            if ctec.window.columns:
                lines.append(f"initial_window_width {ctec.window.columns}c")
            if ctec.window.rows:
                lines.append(f"initial_window_height {ctec.window.rows}c")
            if ctec.window.opacity is not None:
                lines.append(f"background_opacity {ctec.window.opacity}")
            if ctec.window.blur:
                lines.append(f"background_blur {ctec.window.blur}")
            if ctec.window.padding_horizontal is not None:
                lines.append(f"window_padding_width {ctec.window.padding_horizontal}")
            if ctec.window.decorations is not None:
                val = "no" if ctec.window.decorations else "yes"
                lines.append(f"hide_window_decorations {val}")
            if ctec.window.dynamic_title is not None:
                val = "yes" if ctec.window.dynamic_title else "no"
                lines.append(f"dynamic_title {val}")
            lines.append("")

        # Export behavior settings
        if ctec.behavior:
            lines.append("# Behavior")
            if ctec.behavior.shell:
                lines.append(f"shell {ctec.behavior.shell}")
            if ctec.behavior.bell_mode is not None:
                if ctec.behavior.bell_mode == BellMode.NONE:
                    lines.append("enable_audio_bell no")
                    lines.append("visual_bell_duration 0.0")
                elif ctec.behavior.bell_mode == BellMode.VISUAL:
                    lines.append("enable_audio_bell no")
                    lines.append("visual_bell_duration 0.1")
                else:
                    lines.append("enable_audio_bell yes")
            if ctec.behavior.copy_on_select is not None:
                val = "yes" if ctec.behavior.copy_on_select else "no"
                lines.append(f"copy_on_select {val}")
            if ctec.behavior.confirm_close is not None:
                val = "1" if ctec.behavior.confirm_close else "0"
                lines.append(f"confirm_os_window_close {val}")
            if ctec.behavior.close_on_exit:
                val = "yes" if ctec.behavior.close_on_exit == "close" else "no"
                lines.append(f"close_on_child_death {val}")
            lines.append("")

        # Export scroll settings (Kitty uses -1 for unlimited)
        if ctec.scroll:
            lines.append("# Scrollback")
            if ctec.scroll.unlimited:
                lines.append("scrollback_lines -1")
            elif ctec.scroll.disabled:
                lines.append("scrollback_lines 0")
            elif ctec.scroll.lines is not None:
                lines.append(f"scrollback_lines {ctec.scroll.lines}")
            if ctec.scroll.multiplier is not None:
                lines.append(f"wheel_scroll_multiplier {ctec.scroll.multiplier}")
            lines.append("")

        # Export key bindings
        if ctec.key_bindings:
            lines.append("# Key bindings")
            for kb in ctec.key_bindings:
                if kb.mods:
                    keys = "+".join(kb.mods + [kb.key])
                else:
                    keys = kb.key
                lines.append(f"map {keys} {kb.action}")
            lines.append("")

        # Export quick-access-terminal settings (Kitty 0.42+ kitten)
        # Note: These settings are typically placed in quick-access-terminal.conf
        # but we include them here for completeness and cross-terminal compatibility
        if ctec.quick_terminal and ctec.quick_terminal.enabled:
            lines.append(
                "# Quick-access-terminal settings (for quick-access-terminal.conf)"
            )
            if ctec.quick_terminal.position is not None:
                edge = cls.QUICK_TERMINAL_EDGE_REVERSE_MAP.get(
                    ctec.quick_terminal.position, "top"
                )
                lines.append(f"edge {edge}")
            if ctec.quick_terminal.hide_on_focus_loss is not None:
                val = "yes" if ctec.quick_terminal.hide_on_focus_loss else "no"
                lines.append(f"hide_on_focus_loss {val}")
            if ctec.quick_terminal.opacity is not None:
                lines.append(f"background_opacity {ctec.quick_terminal.opacity}")
            lines.append("")

        # Restore terminal-specific settings
        kitty_specific = ctec.get_terminal_specific("kitty")
        if kitty_specific:
            lines.append("# Terminal-specific settings")
            for setting in kitty_specific:
                lines.append(f"{setting.key} {setting.value}")
            lines.append("")

        # Warn about text hints not being supported
        if ctec.text_hints and ctec.text_hints.rules:
            ctec.add_warning(
                f"Kitty does not support text hints/smart selection. "
                f"{len(ctec.text_hints.rules)} hint rule(s) will not be exported. "
                "Consider using Kitty's open_url_with setting for URL handling."
            )

        return "\n".join(lines)
