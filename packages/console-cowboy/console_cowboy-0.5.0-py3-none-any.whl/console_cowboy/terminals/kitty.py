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
    KeyBindingScope,
    PaneConfig,
    QuickTerminalConfig,
    QuickTerminalPosition,
    ScrollConfig,
    TabBarPosition,
    TabBarStyle,
    TabBarVisibility,
    TabConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter
from .mixins import ColorMapMixin, CursorStyleMixin


class KittyAdapter(TerminalAdapter, CursorStyleMixin, ColorMapMixin):
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

    # Kitty color key mappings
    COLOR_KEY_MAP = {
        "foreground": "foreground",
        "background": "background",
        "cursor": "cursor",
        "cursor_text_color": "cursor_text",
        "selection_foreground": "selection_text",
        "selection_background": "selection",
        "url_color": "link",  # Map URL color to CTEC link color
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

    # Tab bar position mapping
    TAB_POSITION_MAP = {
        "top": TabBarPosition.TOP,
        "bottom": TabBarPosition.BOTTOM,
    }

    TAB_POSITION_REVERSE_MAP = {v: k for k, v in TAB_POSITION_MAP.items()}

    # Tab bar style mapping
    TAB_STYLE_MAP = {
        "fade": TabBarStyle.FADE,
        "powerline": TabBarStyle.POWERLINE,
        "slant": TabBarStyle.SLANT,
        "separator": TabBarStyle.SEPARATOR,
        # hidden means visibility=NEVER, not a style
    }

    TAB_STYLE_REVERSE_MAP = {v: k for k, v in TAB_STYLE_MAP.items()}

    @classmethod
    def can_parse(cls, content: str) -> bool:
        """Check if content looks like a Kitty config."""
        # Kitty uses space-separated key value format with specific keys
        kitty_keys = [
            "font_family",
            "font_size",
            "cursor_shape",
            "cursor_blink_interval",
            "background_opacity",
            "window_padding_width",
            "scrollback_lines",
            "enable_audio_bell",
            "color0",
            "color1",
        ]
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if parts and parts[0] in kitty_keys:
                return True
        return False

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
        tabs = TabConfig()
        panes = PaneConfig()

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
                cursor.style = cls.get_cursor_style(value)
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
            elif key == "env":
                # Kitty env format: KEY=VALUE
                if "=" in value:
                    env_key, env_value = value.split("=", 1)
                    if behavior.environment_variables is None:
                        behavior.environment_variables = {}
                    behavior.environment_variables[env_key] = env_value
                else:
                    ctec.add_warning(f"Invalid env entry (missing '='): {value}")
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
                # Kitty: negative value = hide immediately when typing
                # positive = hide after N seconds of inactivity
                # 0 = disabled
                try:
                    wait_value = float(value)
                    behavior.mouse_hide_while_typing = wait_value < 0
                except ValueError:
                    ctec.add_warning(f"Invalid mouse_hide_wait: {value}")
            elif key == "term":
                behavior.terminal_type = value

            # Parse key bindings
            elif key == "map":
                # Format: map <keys> <action>
                # Keys can be:
                # - Simple: ctrl+shift+c
                # - Key sequence (leader keys): ctrl+a>n or ctrl+x>ctrl+y>z
                binding_parts = value.split(None, 1)
                if len(binding_parts) >= 2:
                    keys, action = binding_parts

                    # Check for key sequence (leader keys) with > separator
                    if ">" in keys:
                        # Multi-key sequence like ctrl+a>n or ctrl+x>ctrl+y>z
                        key_sequence = keys.split(">")
                        # Parse the last key in sequence for mods/key
                        last_key = key_sequence[-1]
                        last_key_parts = last_key.split("+")
                        if len(last_key_parts) > 1:
                            mods = last_key_parts[:-1]
                            actual_key = last_key_parts[-1]
                        else:
                            mods = []
                            actual_key = last_key
                        ctec.key_bindings.append(
                            KeyBinding(
                                action=action,
                                key=actual_key,
                                mods=mods,
                                key_sequence=key_sequence,
                            )
                        )
                    else:
                        # Simple keybinding: modifier+key format
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

            # Parse tab settings
            elif key == "tab_bar_edge":
                tabs.position = cls.TAB_POSITION_MAP.get(
                    value.lower(), TabBarPosition.TOP
                )
            elif key == "tab_bar_style":
                if value.lower() == "hidden":
                    tabs.visibility = TabBarVisibility.NEVER
                else:
                    tabs.style = cls.TAB_STYLE_MAP.get(value.lower())
            elif key == "tab_bar_align":
                # Kitty-specific: store in terminal_specific for round-trip
                ctec.add_terminal_specific("kitty", "tab_bar_align", value.lower())
            elif key == "tab_bar_min_tabs":
                try:
                    min_tabs = int(value)
                    # Store raw value in terminal_specific for round-trip
                    ctec.add_terminal_specific("kitty", "tab_bar_min_tabs", min_tabs)
                    # 1 = always show, 2 = show when 2+ tabs (auto)
                    if min_tabs <= 1:
                        tabs.visibility = TabBarVisibility.ALWAYS
                    else:
                        tabs.auto_hide_single = True
                except ValueError:
                    ctec.add_warning(f"Invalid tab_bar_min_tabs: {value}")
            elif key == "tab_switch_strategy":
                # Kitty-specific: store in terminal_specific for round-trip
                ctec.add_terminal_specific(
                    "kitty", "tab_switch_strategy", value.lower()
                )
            elif key == "active_tab_foreground":
                tabs.active_foreground = normalize_color(value)
            elif key == "active_tab_background":
                tabs.active_background = normalize_color(value)
            elif key == "inactive_tab_foreground":
                tabs.inactive_foreground = normalize_color(value)
            elif key == "inactive_tab_background":
                tabs.inactive_background = normalize_color(value)
            elif key == "tab_bar_background":
                tabs.bar_background = normalize_color(value)

            # Parse pane settings
            elif key == "inactive_text_alpha":
                try:
                    panes.inactive_dim_factor = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid inactive_text_alpha: {value}")
            elif key == "active_border_color":
                # Kitty-specific: store in terminal_specific for round-trip
                ctec.add_terminal_specific("kitty", "active_border_color", value)
            elif key == "inactive_border_color":
                # Kitty-specific: store in terminal_specific for round-trip
                ctec.add_terminal_specific("kitty", "inactive_border_color", value)
            elif key == "window_border_width":
                # Kitty-specific: store in terminal_specific for round-trip
                ctec.add_terminal_specific("kitty", "window_border_width", value)
            elif key == "focus_follows_mouse":
                panes.focus_follows_mouse = value.lower() == "yes"

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

            # Handle include directives - warn users that these are not processed
            elif key in ("include", "globinclude", "envinclude"):
                ctec.add_warning(
                    f"Configuration includes ('{key} {value}') are not processed. "
                    "Settings from included files will not be imported. "
                    "Consider consolidating your kitty.conf into a single file."
                )
                # Still store in terminal_specific for visibility
                ctec.add_terminal_specific("kitty", key, value)

            # Handle font_features - OpenType feature settings per font
            # Can appear multiple times, e.g.:
            #   font_features JetBrainsMono-Regular +zero +ss01
            #   font_features FiraCode-Regular +cv02 +ss03
            elif key == "font_features":
                ctec.add_terminal_specific("kitty", key, value)

            # Handle mouse_map - mouse button bindings
            # Can appear multiple times, e.g.:
            #   mouse_map left click ungrabbed mouse_handle_click selection link prompt
            #   mouse_map ctrl+left click ungrabbed mouse_handle_click selection link
            elif key == "mouse_map":
                ctec.add_terminal_specific("kitty", key, value)

            # Handle extended colors (color16 through color255)
            # These are beyond the standard 16 ANSI colors and are terminal-specific
            elif key.startswith("color") and key[5:].isdigit():
                color_num = int(key[5:])
                if color_num >= 16:
                    # Extended colors go to terminal_specific
                    ctec.add_terminal_specific("kitty", key, value)
                else:
                    # This shouldn't happen as 0-15 are in COLOR_KEY_MAP,
                    # but handle gracefully
                    ctec.add_terminal_specific("kitty", key, value)

            # Store all other unrecognized settings in terminal_specific
            # This preserves power user settings like shell_integration,
            # startup_session, macos_* options, wayland_* options, etc.
            else:
                ctec.add_terminal_specific("kitty", key, value)

        # Only add non-empty configs
        if any(
            getattr(scheme, f) is not None
            for f in ["foreground", "background", "black", "link"]
        ):
            ctec.color_scheme = scheme
        if font.family or font.size or font.symbol_map or font.ligatures is not None:
            ctec.font = font
        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor
        if window.columns or window.rows or window.opacity:
            ctec.window = window
        if (
            behavior.shell
            or behavior.scrollback_lines
            or behavior.bell_mode
            or behavior.environment_variables
            or behavior.mouse_hide_while_typing is not None
            or behavior.terminal_type
        ):
            ctec.behavior = behavior
        if quick_terminal.enabled:
            ctec.quick_terminal = quick_terminal
        # Add tabs if any tab settings were configured
        if any(
            getattr(tabs, f) is not None
            for f in [
                "position",
                "visibility",
                "style",
                "auto_hide_single",
                "active_foreground",
                "active_background",
                "inactive_foreground",
                "inactive_background",
                "bar_background",
            ]
        ):
            ctec.tabs = tabs
        # Add panes if any pane settings were configured
        if any(
            getattr(panes, f) is not None
            for f in [
                "inactive_dim_factor",
                "focus_follows_mouse",
            ]
        ):
            ctec.panes = panes

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC to Kitty configuration format."""
        lines = ["# Kitty configuration", "# Generated by console-cowboy", ""]

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            lines.append("# Colors")
            colors = cls.map_ctec_to_colors(scheme)
            for kitty_key, color_hex in colors.items():
                lines.append(f"{kitty_key} {color_hex}")
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
                style = cls.get_cursor_style_value(ctec.cursor.style, "block")
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
            if ctec.behavior.shell_args:
                # Kitty doesn't have separate shell args, warn the user
                ctec.add_warning(
                    "Kitty does not support separate shell arguments. "
                    "Consider using a shell wrapper script or combining the "
                    "command with arguments."
                )
            if ctec.behavior.environment_variables:
                for env_key, env_value in ctec.behavior.environment_variables.items():
                    lines.append(f"env {env_key}={env_value}")
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
            if ctec.behavior.mouse_hide_while_typing is not None:
                # Kitty: negative value = hide immediately when typing
                # Use -1 for true, 3.0 (default) for false
                val = "-1" if ctec.behavior.mouse_hide_while_typing else "3.0"
                lines.append(f"mouse_hide_wait {val}")
            if ctec.behavior.terminal_type:
                lines.append(f"term {ctec.behavior.terminal_type}")
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
                # Check for unsupported features and warn
                if kb.scope and kb.scope == KeyBindingScope.GLOBAL:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has global scope which is not supported "
                        "in Kitty. It will be exported as a regular (application-scoped) binding. "
                        "Consider using Kitty's quick-access-terminal kitten for global hotkeys."
                    )
                if kb.mode:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has mode restriction '{kb.mode}' which is not "
                        "supported in Kitty. It will be exported without mode restrictions."
                    )

                # Handle key sequences (leader keys)
                if kb.key_sequence:
                    # Kitty supports key sequences with > separator
                    keys = ">".join(kb.key_sequence)
                elif kb.mods:
                    keys = "+".join(kb.mods + [kb.key])
                else:
                    keys = kb.key

                # Format action - Kitty uses space-separated parameters, not colon
                if kb.action_param:
                    action = f"{kb.action} {kb.action_param}"
                else:
                    action = kb.action
                lines.append(f"map {keys} {action}")
            lines.append("")

        # Export tab settings
        if ctec.tabs:
            lines.append("# Tab Bar")
            if ctec.tabs.position is not None:
                position = cls.TAB_POSITION_REVERSE_MAP.get(ctec.tabs.position, "top")
                lines.append(f"tab_bar_edge {position}")
            # Handle visibility - Kitty uses tab_bar_style=hidden or tab_bar_min_tabs
            # Check for Kitty-specific min_tabs value in terminal_specific first
            min_tabs_specific = ctec.get_terminal_specific("kitty", "tab_bar_min_tabs")
            if ctec.tabs.visibility == TabBarVisibility.NEVER:
                lines.append("tab_bar_style hidden")
            elif min_tabs_specific is not None:
                # Use the exact min_tabs value from terminal_specific (round-trip)
                lines.append(f"tab_bar_min_tabs {min_tabs_specific}")
            elif ctec.tabs.visibility == TabBarVisibility.ALWAYS:
                lines.append("tab_bar_min_tabs 1")
            elif ctec.tabs.auto_hide_single:
                lines.append("tab_bar_min_tabs 2")
            # Export style (only if visibility != hidden)
            if (
                ctec.tabs.style is not None
                and ctec.tabs.visibility != TabBarVisibility.NEVER
            ):
                style = cls.TAB_STYLE_REVERSE_MAP.get(ctec.tabs.style)
                if style:
                    lines.append(f"tab_bar_style {style}")
            # Export Kitty-specific tab settings from terminal_specific (round-trip)
            align_specific = ctec.get_terminal_specific("kitty", "tab_bar_align")
            if align_specific:
                lines.append(f"tab_bar_align {align_specific}")
            strategy_specific = ctec.get_terminal_specific(
                "kitty", "tab_switch_strategy"
            )
            if strategy_specific:
                lines.append(f"tab_switch_strategy {strategy_specific}")
            # Tab colors
            if ctec.tabs.active_foreground is not None:
                lines.append(
                    f"active_tab_foreground {ctec.tabs.active_foreground.to_hex()}"
                )
            if ctec.tabs.active_background is not None:
                lines.append(
                    f"active_tab_background {ctec.tabs.active_background.to_hex()}"
                )
            if ctec.tabs.inactive_foreground is not None:
                lines.append(
                    f"inactive_tab_foreground {ctec.tabs.inactive_foreground.to_hex()}"
                )
            if ctec.tabs.inactive_background is not None:
                lines.append(
                    f"inactive_tab_background {ctec.tabs.inactive_background.to_hex()}"
                )
            if ctec.tabs.bar_background is not None:
                lines.append(f"tab_bar_background {ctec.tabs.bar_background.to_hex()}")
            # Warn about unsupported tab features
            unsupported = []
            if ctec.tabs.new_tab_position is not None:
                unsupported.append("new_tab_position")
            if ctec.tabs.max_width is not None:
                unsupported.append("max_width")
            if ctec.tabs.show_index is not None:
                unsupported.append("show_index")
            if ctec.tabs.inherit_working_directory is not None:
                unsupported.append("inherit_working_directory")
            if unsupported:
                ctec.add_warning(
                    f"Kitty does not support: {', '.join(unsupported)}. "
                    "These tab settings will not be exported."
                )
            lines.append("")

        # Export pane settings
        if ctec.panes:
            lines.append("# Pane Settings")
            if ctec.panes.inactive_dim_factor is not None:
                lines.append(f"inactive_text_alpha {ctec.panes.inactive_dim_factor}")
            if ctec.panes.focus_follows_mouse is not None:
                val = "yes" if ctec.panes.focus_follows_mouse else "no"
                lines.append(f"focus_follows_mouse {val}")
            # Warn about unsupported pane features
            unsupported = []
            if ctec.panes.inactive_dim_color is not None:
                unsupported.append("inactive_dim_color")
            if ctec.panes.divider_color is not None:
                unsupported.append("divider_color")
            if unsupported:
                ctec.add_warning(
                    f"Kitty does not support: {', '.join(unsupported)}. "
                    "These pane settings will not be exported."
                )
            lines.append("")

        # Export Kitty-specific pane border settings from terminal_specific (round-trip)
        border_width = ctec.get_terminal_specific("kitty", "window_border_width")
        active_border = ctec.get_terminal_specific("kitty", "active_border_color")
        inactive_border = ctec.get_terminal_specific("kitty", "inactive_border_color")
        if border_width or active_border or inactive_border:
            if not ctec.panes:
                # Add header if not already present from above
                lines.append("# Pane Settings")
            if border_width:
                lines.append(f"window_border_width {border_width}")
            if active_border:
                lines.append(f"active_border_color {active_border}")
            if inactive_border:
                lines.append(f"inactive_border_color {inactive_border}")
            if not ctec.panes:
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
