"""
Ghostty configuration adapter.

Ghostty uses a simple key=value configuration format stored in
~/.config/ghostty/config
"""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BackgroundImagePosition,
    BackgroundImageScale,
    BehaviorConfig,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    KeyBinding,
    KeyBindingScope,
    NewTabPosition,
    PaneConfig,
    QuickTerminalConfig,
    QuickTerminalPosition,
    QuickTerminalScreen,
    ScrollConfig,
    TabBarPosition,
    TabBarVisibility,
    TabConfig,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color
from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

from .base import TerminalAdapter
from .mixins import ColorMapMixin, CursorStyleMixin, ParsingMixin


class GhosttyAdapter(TerminalAdapter, CursorStyleMixin, ColorMapMixin, ParsingMixin):
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
    }

    # Cursor style mapping
    CURSOR_STYLE_MAP = {
        "block": CursorStyle.BLOCK,
        "bar": CursorStyle.BEAM,
        "underline": CursorStyle.UNDERLINE,
    }

    # Quick terminal position mapping
    QUICK_TERMINAL_POSITION_MAP = {
        "top": QuickTerminalPosition.TOP,
        "bottom": QuickTerminalPosition.BOTTOM,
        "left": QuickTerminalPosition.LEFT,
        "right": QuickTerminalPosition.RIGHT,
        "center": QuickTerminalPosition.CENTER,
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

    # Font mapping
    FONT_MAPPING = {
        "font-family": ("family", str),
        "font-size": ("size", float),
        "font-family-bold": ("bold_font", str),
        "font-family-italic": ("italic_font", str),
        "font-family-bold-italic": ("bold_italic_font", str),
        "adjust-cell-height": (
            "line_height",
            lambda v: 1.0 + float(v.rstrip("%")) / 100,
        ),
    }
    # Note: adjust-cell-width handled separately in parse() method
    # due to pixel vs percentage handling - see the elif key == "adjust-cell-width" block

    # Window mapping
    WINDOW_MAPPING = {
        "window-width": ("columns", int),
        "window-height": ("rows", int),
        "background-opacity": ("opacity", float),
        "background-blur-radius": ("blur", int),
        "window-padding-x": ("padding_horizontal", int),
        "window-padding-y": ("padding_vertical", int),
        "window-decoration": ("decorations", lambda v: v.lower() != "none"),
        "window-title-show-all": ("dynamic_title", lambda v: v.lower() == "true"),
        "background-image": ("background_image", str),
        "background-image-opacity": ("background_image_opacity", float),
    }

    # Background image scale mapping (Ghostty: background-image-fit)
    BACKGROUND_IMAGE_SCALE_MAP = {
        "contain": BackgroundImageScale.CONTAIN,
        "cover": BackgroundImageScale.COVER,
        "stretch": BackgroundImageScale.STRETCH,
        "none": BackgroundImageScale.NONE,
    }

    BACKGROUND_IMAGE_SCALE_REVERSE_MAP = {
        v: k for k, v in BACKGROUND_IMAGE_SCALE_MAP.items()
    }

    # Background image position mapping
    BACKGROUND_IMAGE_POSITION_MAP = {
        "top-left": BackgroundImagePosition.TOP_LEFT,
        "top-center": BackgroundImagePosition.TOP_CENTER,
        "top-right": BackgroundImagePosition.TOP_RIGHT,
        "center-left": BackgroundImagePosition.CENTER_LEFT,
        "center": BackgroundImagePosition.CENTER,
        "center-right": BackgroundImagePosition.CENTER_RIGHT,
        "bottom-left": BackgroundImagePosition.BOTTOM_LEFT,
        "bottom-center": BackgroundImagePosition.BOTTOM_CENTER,
        "bottom-right": BackgroundImagePosition.BOTTOM_RIGHT,
    }

    BACKGROUND_IMAGE_POSITION_REVERSE_MAP = {
        v: k for k, v in BACKGROUND_IMAGE_POSITION_MAP.items()
    }

    # Behavior mapping
    BEHAVIOR_MAPPING = {
        "command": ("shell", str),
        "working-directory": ("working_directory", str),
        "copy-on-select": ("copy_on_select", lambda v: v.lower() == "true"),
        "confirm-close-surface": ("confirm_close", lambda v: v.lower() == "true"),
        "mouse-hide-while-typing": (
            "mouse_hide_while_typing",
            lambda v: v.lower() == "true",
        ),
        "term": ("terminal_type", str),
    }

    # Tab bar visibility mapping
    TAB_VISIBILITY_MAP = {
        "always": TabBarVisibility.ALWAYS,
        "auto": TabBarVisibility.AUTO,
        "never": TabBarVisibility.NEVER,
    }

    TAB_VISIBILITY_REVERSE_MAP = {v: k for k, v in TAB_VISIBILITY_MAP.items()}

    # Tab position mapping (GTK-specific)
    TAB_POSITION_MAP = {
        "top": TabBarPosition.TOP,
        "bottom": TabBarPosition.BOTTOM,
        "left": TabBarPosition.TOP,  # Map left to top (closest equivalent)
        "right": TabBarPosition.BOTTOM,  # Map right to bottom (closest equivalent)
    }

    # Reverse map - prefer canonical top/bottom values over left/right
    TAB_POSITION_REVERSE_MAP = {
        TabBarPosition.TOP: "top",
        TabBarPosition.BOTTOM: "bottom",
    }

    # New tab position mapping
    NEW_TAB_POSITION_MAP = {
        "current": NewTabPosition.CURRENT,
        "end": NewTabPosition.END,
    }

    NEW_TAB_POSITION_REVERSE_MAP = {v: k for k, v in NEW_TAB_POSITION_MAP.items()}

    @classmethod
    def can_parse(cls, content: str) -> bool:
        """Check if content looks like a Ghostty config."""
        # Ghostty uses key=value format with specific keys
        ghostty_keys = [
            "font-family",
            "font-size",
            "cursor-color",
            "cursor-style",
            "palette",
            "background-opacity",
            "window-padding-x",
            "quick-terminal-position",
        ]
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=")[0].strip()
                if key in ghostty_keys:
                    return True
        return False

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
    def _parse_keybind(cls, value: str, ctec: CTEC) -> KeyBinding | None:
        """
        Parse a Ghostty keybind value into a KeyBinding.

        Ghostty keybind format:
        - Basic: modifier+key=action or modifier+key=action:param
        - Prefixes: global:, unconsumed:, all:, physical: (can be combined)
        - Key sequences: ctrl+a>n=new_window (leader key followed by another key)
        - Unbind: keybind = ctrl+c=unbind or keybind = performable:unbind

        Examples:
        - keybind = ctrl+shift+c=copy_to_clipboard
        - keybind = ctrl+grave=toggle_quick_terminal
        - keybind = global:ctrl+grave=toggle_quick_terminal
        - keybind = unconsumed:ctrl+shift+g=write_screen_file
        - keybind = ctrl+a>n=new_window
        - keybind = ctrl+shift+enter=new_split:right
        - keybind = physical:ctrl+grave=toggle_quick_terminal
        - keybind = all:ctrl+shift+p=command_palette
        """
        value = value.strip()
        if not value:
            return None

        # Store the raw value for perfect round-trip
        raw_value = value

        # Parse prefixes
        scope: KeyBindingScope | None = None
        physical_key: bool | None = None
        consume: bool | None = None

        # Process prefixes - they can be combined (e.g., global:physical:)
        while ":" in value:
            # Check if this colon is a prefix separator or an action parameter
            first_colon = value.index(":")
            potential_prefix = value[:first_colon].lower()

            if potential_prefix == "global":
                scope = KeyBindingScope.GLOBAL
                value = value[first_colon + 1 :]
            elif potential_prefix == "unconsumed":
                scope = KeyBindingScope.UNCONSUMED
                consume = False
                value = value[first_colon + 1 :]
            elif potential_prefix == "all":
                scope = KeyBindingScope.ALL
                value = value[first_colon + 1 :]
            elif potential_prefix == "physical":
                physical_key = True
                value = value[first_colon + 1 :]
            elif potential_prefix == "performable":
                # performable: prefix - skip it, it's Ghostty-specific behavior modifier
                value = value[first_colon + 1 :]
            else:
                # Not a prefix, must be part of the key=action:param format
                break

        # Now parse the key=action part
        if "=" not in value:
            ctec.add_warning(f"Invalid keybind (missing '='): {raw_value}")
            return None

        key_part, action_part = value.split("=", 1)
        key_part = key_part.strip()
        action_part = action_part.strip()

        # Handle special "unbind" action
        if action_part.lower() == "unbind":
            # Unbind entries are terminal-specific, we can't represent them in CTEC
            # Store as terminal-specific for round-trip
            ctec.add_terminal_specific(
                "ghostty", f"keybind_unbind:{key_part}", raw_value
            )
            return None

        # Parse action and optional parameter (action:param)
        action = action_part
        action_param: str | None = None
        if ":" in action_part:
            action, action_param = action_part.split(":", 1)

        # Parse key sequence (e.g., ctrl+a>n for leader key)
        key_sequence: list[str] | None = None
        if ">" in key_part:
            # This is a key sequence
            key_sequence = key_part.split(">")
            # For key sequences, the key and mods fields hold the last key in the sequence
            last_key_part = key_sequence[-1] if key_sequence else key_part
            mods, key = cls._parse_key_with_mods(last_key_part)
        else:
            mods, key = cls._parse_key_with_mods(key_part)

        return KeyBinding(
            action=action,
            key=key,
            mods=mods,
            action_param=action_param,
            scope=scope,
            key_sequence=key_sequence,
            physical_key=physical_key,
            consume=consume,
            _raw=raw_value,
        )

    @classmethod
    def _parse_key_with_mods(cls, key_str: str) -> tuple[list[str], str]:
        """
        Parse a key string with modifiers into (mods, key).

        Examples:
        - "ctrl+shift+c" -> (["ctrl", "shift"], "c")
        - "grave" -> ([], "grave")
        - "super+return" -> (["super"], "return")
        """
        parts = key_str.split("+")
        if len(parts) == 1:
            return [], parts[0]

        # The last part is the key, everything else is modifiers
        key = parts[-1]
        mods = [m.lower() for m in parts[:-1]]
        return mods, key

    @classmethod
    def _format_keybind(cls, kb: KeyBinding) -> str:
        """
        Format a KeyBinding as a Ghostty keybind value.

        Returns the value part after 'keybind = '.
        """
        # If we have the raw value, use it for perfect round-trip
        if kb._raw and kb._raw.strip():
            return kb._raw

        parts = []

        # Add scope prefix if not default
        if kb.scope == KeyBindingScope.GLOBAL:
            parts.append("global:")
        elif kb.scope == KeyBindingScope.UNCONSUMED:
            parts.append("unconsumed:")
        elif kb.scope == KeyBindingScope.ALL:
            parts.append("all:")

        # Add physical prefix if set
        if kb.physical_key:
            parts.append("physical:")

        # Build the key part
        if kb.key_sequence:
            key_part = ">".join(kb.key_sequence)
        else:
            if kb.mods:
                key_part = "+".join(kb.mods + [kb.key])
            else:
                key_part = kb.key

        # Build the action part
        action_part = kb.action
        if kb.action_param:
            action_part = f"{kb.action}:{kb.action_param}"

        parts.append(f"{key_part}={action_part}")

        return "".join(parts)

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

            if "=" not in line:
                ctec.add_warning(f"Invalid line (no '='): {line}")
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            def on_error(k, v, e):
                ctec.add_warning(f"Invalid {k}: {v}")

            # Check if it's a theme name
            if key == "theme":
                # Handle special Ghostty theme formats
                if "light:" in value and "dark:" in value:
                    # Ghostty light/dark syntax: "light:Theme A,dark:Theme B"
                    ctec.add_warning(
                        f"Ghostty light/dark theme syntax '{value}' is terminal-specific. "
                        "The dark theme will be used when converting to other terminals."
                    )
                    # Store full value for round-trip
                    ctec.add_terminal_specific("ghostty", "theme_light_dark", value)
                    # Extract dark theme for cross-terminal compatibility
                    for part in value.split(","):
                        part = part.strip()
                        if part.startswith("dark:"):
                            scheme.name = part[5:].strip()
                            break
                elif value.startswith("/") or value.startswith("~"):
                    # Absolute path to theme file
                    ctec.add_warning(
                        f"Ghostty theme path '{value}' cannot be converted to other terminals. "
                        "Stored as terminal-specific setting."
                    )
                    ctec.add_terminal_specific("ghostty", "theme_path", value)
                else:
                    # Simple theme name
                    scheme.name = value
            # Check if it's a standard color key
            elif ctec_color_key := cls.get_ctec_color_key(key):
                setattr(scheme, ctec_color_key, normalize_color(value))
            # Handle special palette color
            elif key == "palette":
                # Format: index=color (e.g., "0=#1d1f21")
                if "=" in value:
                    idx_str, color_str = value.split("=", 1)
                    try:
                        idx = int(idx_str)
                        cls._parse_palette_color(idx, color_str, scheme)
                    except ValueError:
                        ctec.add_warning(f"Invalid palette entry: {value}")

            # Parse mappings
            elif cls.apply_line_mapping(key, value, font, cls.FONT_MAPPING, on_error):
                pass
            elif cls.apply_line_mapping(
                key, value, window, cls.WINDOW_MAPPING, on_error
            ):
                pass
            elif cls.apply_line_mapping(
                key, value, behavior, cls.BEHAVIOR_MAPPING, on_error
            ):
                pass

            # Handle special cases that didn't fit into simple mappings
            elif key == "adjust-cell-width":
                # Ghostty accepts both pixel values (2) and percentages (5%)
                if "%" in value:
                    # Percentage: convert to multiplier
                    try:
                        pct = float(value.rstrip("%"))
                        font.cell_width = 1.0 + pct / 100
                    except ValueError:
                        ctec.add_warning(f"Invalid adjust-cell-width: {value}")
                else:
                    # Pixel value: store as terminal-specific since we can't
                    # convert to multiplier without knowing font size
                    try:
                        px = int(value)
                        ctec.add_terminal_specific("ghostty", "adjust-cell-width", px)
                        ctec.add_warning(
                            f"Ghostty adjust-cell-width pixel value ({px}) cannot be "
                            "converted to a multiplier. Stored as terminal-specific."
                        )
                    except ValueError:
                        ctec.add_warning(f"Invalid adjust-cell-width: {value}")

            elif key == "font-feature":
                # Ghostty allows multiple font-feature lines
                if font.font_features is None:
                    font.font_features = []
                font.font_features.append(value)

            elif key == "fullscreen":
                if value.lower() == "true":
                    window.startup_mode = "fullscreen"

            # Parse background image scale (fit) and position
            elif key == "background-image-fit":
                scale = cls.BACKGROUND_IMAGE_SCALE_MAP.get(value.lower())
                if scale:
                    window.background_image_scale = scale
                else:
                    ctec.add_warning(f"Unknown background-image-fit value: {value}")

            elif key == "background-image-position":
                position = cls.BACKGROUND_IMAGE_POSITION_MAP.get(value.lower())
                if position:
                    window.background_image_position = position
                else:
                    ctec.add_warning(f"Unknown background-image-position: {value}")

            elif key == "background-image-repeat":
                # If repeat is true, treat it as tile mode
                if value.lower() == "true":
                    window.background_image_scale = BackgroundImageScale.TILE

            # Parse cursor settings
            elif key == "cursor-style":
                cursor.style = cls.get_cursor_style(value)
            elif key == "cursor-style-blink":
                cursor.blink = value.lower() == "true"

            # Parse behavior settings (env requires special handling - multiple values)
            elif key == "env":
                # Ghostty env format: KEY=VALUE
                if "=" in value:
                    env_key, env_value = value.split("=", 1)
                    if behavior.environment_variables is None:
                        behavior.environment_variables = {}
                    behavior.environment_variables[env_key] = env_value
                else:
                    ctec.add_warning(f"Invalid env entry (missing '='): {value}")
            elif key == "scrollback-limit":
                try:
                    # Ghostty uses bytes, not lines - convert to ScrollConfig
                    byte_count = int(value)
                    ctec.scroll = ScrollConfig.from_bytes(byte_count)
                except ValueError:
                    ctec.add_warning(f"Invalid scrollback-limit: {value}")
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
            elif key == "quick-terminal-size":
                quick_terminal.enabled = True
                # Store raw size string (supports "50%", "300px", "50%,500px")
                quick_terminal.size = value
            elif key == "quick-terminal-autohide":
                quick_terminal.enabled = True
                quick_terminal.hide_on_focus_loss = value.lower() == "true"

            # Parse tab settings
            elif key == "window-show-tab-bar":
                tabs.visibility = cls.TAB_VISIBILITY_MAP.get(
                    value.lower(), TabBarVisibility.AUTO
                )
            elif key == "gtk-tabs-location":
                # GTK-specific tab position
                val_lower = value.lower()
                tabs.position = cls.TAB_POSITION_MAP.get(val_lower, TabBarPosition.TOP)
                # Warn when approximating left/right to top/bottom
                if val_lower in ("left", "right"):
                    ctec.add_warning(
                        f"Ghostty gtk-tabs-location '{value}' is approximated to "
                        f"'{'top' if val_lower == 'left' else 'bottom'}' for cross-terminal compatibility."
                    )
            elif key == "window-new-tab-position":
                tabs.new_tab_position = cls.NEW_TAB_POSITION_MAP.get(
                    value.lower(), NewTabPosition.CURRENT
                )
            elif key == "window-inherit-working-directory":
                tabs.inherit_working_directory = value.lower() == "true"

            # Parse pane settings
            elif key == "unfocused-split-opacity":
                try:
                    panes.inactive_dim_factor = float(value)
                except ValueError:
                    ctec.add_warning(f"Invalid unfocused-split-opacity: {value}")
            elif key == "unfocused-split-fill":
                panes.inactive_dim_color = normalize_color(value)
            elif key == "split-divider-color":
                panes.divider_color = normalize_color(value)
            elif key == "focus-follows-mouse":
                panes.focus_follows_mouse = value.lower() == "true"

            # Parse keybindings
            elif key == "keybind":
                kb = cls._parse_keybind(value, ctec)
                if kb:
                    ctec.key_bindings.append(kb)

            # Store unrecognized settings as terminal-specific
            else:
                ctec.add_terminal_specific("ghostty", key, value)

        # Only add non-empty configs
        if scheme.name or any(
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
        if (
            font.family
            or font.size
            or font.font_features
            or font.cell_width
            or font.line_height
        ):
            ctec.font = font
        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor
        if (
            window.columns
            or window.rows
            or window.opacity
            or window.background_image
            or window.background_image_opacity is not None
            or window.background_image_scale
            or window.background_image_position
        ):
            ctec.window = window
        if (
            behavior.shell
            or behavior.scrollback_lines
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
                "visibility",
                "position",
                "new_tab_position",
                "inherit_working_directory",
            ]
        ):
            ctec.tabs = tabs
        # Add panes if any pane settings were configured
        if any(
            getattr(panes, f) is not None
            for f in [
                "inactive_dim_factor",
                "inactive_dim_color",
                "divider_color",
                "focus_follows_mouse",
            ]
        ):
            ctec.panes = panes

        return ctec

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC to Ghostty configuration format."""
        lines = ["# Ghostty configuration", "# Generated by console-cowboy", ""]

        # Export colors
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            lines.append("# Colors")

            # Export theme name if set
            if scheme.name:
                lines.append(f"theme = {scheme.name}")

            # Use mixin to export standard colors
            colors = cls.map_ctec_to_colors(scheme)
            for ghostty_key, color_hex in colors.items():
                lines.append(f"{ghostty_key} = {color_hex}")

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
                lines.append(f"adjust-cell-height = {adjust}%")
            if ctec.font.cell_width and ctec.font.cell_width != 1.0:
                adjust = int((ctec.font.cell_width - 1.0) * 100)
                lines.append(f"adjust-cell-width = {adjust}%")
            if ctec.font.font_features:
                for feature in ctec.font.font_features:
                    lines.append(f"font-feature = {feature}")
            lines.append("")

        # Export cursor settings
        if ctec.cursor:
            lines.append("# Cursor")
            if ctec.cursor.style:
                style = cls.get_cursor_style_value(ctec.cursor.style, "block")
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
                # Use 'auto' for decorations=True (cross-platform compatible)
                # Use 'none' for decorations=False
                # Note: On Linux/GTK, valid values are: auto, client, server, none
                # 'true' is not valid on Linux/GTK
                val = "auto" if ctec.window.decorations else "none"
                lines.append(f"window-decoration = {val}")
            if ctec.window.startup_mode == "fullscreen":
                lines.append("fullscreen = true")
            if ctec.window.dynamic_title is not None:
                lines.append(
                    f"window-title-show-all = {str(ctec.window.dynamic_title).lower()}"
                )
            # Export background image settings
            if ctec.window.background_image:
                lines.append(f"background-image = {ctec.window.background_image}")
            if ctec.window.background_image_opacity is not None:
                lines.append(
                    f"background-image-opacity = {ctec.window.background_image_opacity}"
                )
            if ctec.window.background_image_scale is not None:
                if ctec.window.background_image_scale == BackgroundImageScale.TILE:
                    # Ghostty uses repeat for tiling
                    lines.append("background-image-repeat = true")
                elif (
                    ctec.window.background_image_scale == BackgroundImageScale.CENTERED
                ):
                    # Ghostty doesn't support centered mode, fall back to contain
                    ctec.add_warning(
                        "Ghostty does not support 'centered' background image scaling. "
                        "Using 'contain' as fallback."
                    )
                    lines.append("background-image-fit = contain")
                else:
                    fit_val = cls.BACKGROUND_IMAGE_SCALE_REVERSE_MAP.get(
                        ctec.window.background_image_scale
                    )
                    if fit_val:
                        lines.append(f"background-image-fit = {fit_val}")
            if ctec.window.background_image_position is not None:
                pos_val = cls.BACKGROUND_IMAGE_POSITION_REVERSE_MAP.get(
                    ctec.window.background_image_position
                )
                if pos_val:
                    lines.append(f"background-image-position = {pos_val}")
            lines.append("")

        # Export behavior settings
        if ctec.behavior:
            lines.append("# Behavior")
            if ctec.behavior.shell:
                lines.append(f"command = {ctec.behavior.shell}")
            if ctec.behavior.shell_args:
                # Ghostty doesn't have separate shell args, warn the user
                ctec.add_warning(
                    "Ghostty does not support separate shell arguments. "
                    "Consider using a shell wrapper script or combining the "
                    "command with arguments."
                )
            if ctec.behavior.working_directory:
                lines.append(f"working-directory = {ctec.behavior.working_directory}")
            if ctec.behavior.environment_variables:
                for env_key, env_value in ctec.behavior.environment_variables.items():
                    lines.append(f"env = {env_key}={env_value}")
            if ctec.behavior.copy_on_select is not None:
                lines.append(
                    f"copy-on-select = {str(ctec.behavior.copy_on_select).lower()}"
                )
            if ctec.behavior.confirm_close is not None:
                lines.append(
                    f"confirm-close-surface = {str(ctec.behavior.confirm_close).lower()}"
                )
            if ctec.behavior.mouse_hide_while_typing is not None:
                lines.append(
                    f"mouse-hide-while-typing = "
                    f"{str(ctec.behavior.mouse_hide_while_typing).lower()}"
                )
            if ctec.behavior.terminal_type:
                lines.append(f"term = {ctec.behavior.terminal_type}")
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
            if ctec.quick_terminal.size is not None:
                lines.append(f"quick-terminal-size = {ctec.quick_terminal.size}")
            if ctec.quick_terminal.hide_on_focus_loss is not None:
                lines.append(
                    f"quick-terminal-autohide = "
                    f"{str(ctec.quick_terminal.hide_on_focus_loss).lower()}"
                )
            # Export quick terminal hotkey as a global keybinding
            # This converts iTerm2's numeric key code + modifiers to Ghostty format
            if (
                ctec.quick_terminal.hotkey_key_code is not None
                or ctec.quick_terminal.hotkey_modifiers is not None
            ):
                keybind_str = macos_hotkey_to_keybind(
                    ctec.quick_terminal.hotkey_key_code,
                    ctec.quick_terminal.hotkey_modifiers,
                )
                if keybind_str:
                    lines.append(f"keybind = {keybind_str}")
                else:
                    ctec.add_warning(
                        f"Could not convert quick terminal hotkey (key code: "
                        f"{ctec.quick_terminal.hotkey_key_code}) to keybinding. "
                        "You may need to manually configure the global keybind."
                    )
            lines.append("")

        # Export tab settings
        if ctec.tabs:
            lines.append("# Tab Bar")
            if ctec.tabs.visibility is not None:
                visibility = cls.TAB_VISIBILITY_REVERSE_MAP.get(
                    ctec.tabs.visibility, "auto"
                )
                lines.append(f"window-show-tab-bar = {visibility}")
            if ctec.tabs.position is not None:
                position = cls.TAB_POSITION_REVERSE_MAP.get(ctec.tabs.position, "top")
                lines.append(f"gtk-tabs-location = {position}")
            if ctec.tabs.new_tab_position is not None:
                new_pos = cls.NEW_TAB_POSITION_REVERSE_MAP.get(
                    ctec.tabs.new_tab_position, "current"
                )
                lines.append(f"window-new-tab-position = {new_pos}")
            if ctec.tabs.inherit_working_directory is not None:
                lines.append(
                    f"window-inherit-working-directory = "
                    f"{str(ctec.tabs.inherit_working_directory).lower()}"
                )
            # Warn about unsupported tab features
            unsupported = []
            if ctec.tabs.style is not None:
                unsupported.append("style")
            if ctec.tabs.max_width is not None:
                unsupported.append("max_width")
            if ctec.tabs.show_index is not None:
                unsupported.append("show_index")
            if any(
                getattr(ctec.tabs, f) is not None
                for f in [
                    "active_foreground",
                    "active_background",
                    "inactive_foreground",
                    "inactive_background",
                    "bar_background",
                ]
            ):
                unsupported.append("tab colors")
            if unsupported:
                ctec.add_warning(
                    f"Ghostty does not support: {', '.join(unsupported)}. "
                    "These tab settings will not be exported."
                )
            lines.append("")

        # Export pane settings
        if ctec.panes:
            lines.append("# Pane Settings")
            if ctec.panes.inactive_dim_factor is not None:
                # Ghostty minimum is 0.15, clamp values
                dim = max(0.15, ctec.panes.inactive_dim_factor)
                if dim != ctec.panes.inactive_dim_factor:
                    ctec.add_warning(
                        f"Ghostty minimum unfocused-split-opacity is 0.15. "
                        f"Value {ctec.panes.inactive_dim_factor} was clamped to 0.15."
                    )
                lines.append(f"unfocused-split-opacity = {dim}")
            if ctec.panes.inactive_dim_color is not None:
                lines.append(
                    f"unfocused-split-fill = {ctec.panes.inactive_dim_color.to_hex()}"
                )
            if ctec.panes.divider_color is not None:
                lines.append(
                    f"split-divider-color = {ctec.panes.divider_color.to_hex()}"
                )
            if ctec.panes.focus_follows_mouse is not None:
                lines.append(
                    f"focus-follows-mouse = "
                    f"{str(ctec.panes.focus_follows_mouse).lower()}"
                )
            lines.append("")

        # Export keybindings
        if ctec.key_bindings:
            lines.append("# Key bindings")
            for kb in ctec.key_bindings:
                # Warn about unsupported features
                if kb.mode:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has mode restriction '{kb.mode}' which is not "
                        "supported in Ghostty. It will be exported without mode restrictions."
                    )
                keybind_value = cls._format_keybind(kb)
                lines.append(f"keybind = {keybind_value}")
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
