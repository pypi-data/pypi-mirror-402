"""
Hyper terminal adapter for Console Cowboy.

Hyper is an Electron-based terminal emulator with a JavaScript configuration file.
The config file is located at:
- macOS: ~/Library/Application Support/Hyper/.hyper.js
- Windows: %APPDATA%/Hyper/.hyper.js
- Linux: ~/.config/Hyper/.hyper.js

The configuration format is a CommonJS module that exports an object with:
- config: Main configuration options
- plugins: List of plugin names
- localPlugins: List of local plugin paths
- keymaps: Custom keyboard shortcuts
"""

from pathlib import Path
from typing import Any

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
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
from console_cowboy.terminals.base import TerminalAdapter

from .javascript import execute_hyper_config, parse_hyper_color


class HyperAdapter(TerminalAdapter):
    """Adapter for Hyper terminal emulator."""

    name = "hyper"
    display_name = "Hyper"
    description = "Hyper terminal emulator (Electron-based)"
    config_extensions = [".js"]
    default_config_paths = [
        ".config/Hyper/.hyper.js",  # Linux
        "Library/Application Support/Hyper/.hyper.js",  # macOS
    ]

    # Mapping of Hyper cursor shapes to CTEC cursor styles
    CURSOR_STYLE_MAP = {
        "BLOCK": CursorStyle.BLOCK,
        "BEAM": CursorStyle.BEAM,
        "UNDERLINE": CursorStyle.UNDERLINE,
    }

    # Reverse mapping for export
    CURSOR_STYLE_EXPORT_MAP = {
        CursorStyle.BLOCK: "BLOCK",
        CursorStyle.BEAM: "BEAM",
        CursorStyle.UNDERLINE: "UNDERLINE",
    }

    # Hyper color palette keys (ANSI 0-15)
    ANSI_COLOR_KEYS = [
        "black",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "white",
        "lightBlack",
        "lightRed",
        "lightGreen",
        "lightYellow",
        "lightBlue",
        "lightMagenta",
        "lightCyan",
        "lightWhite",
    ]

    # Mapping of Hyper ANSI colors to CTEC color scheme fields
    ANSI_TO_CTEC_MAP = {
        "black": "black",
        "red": "red",
        "green": "green",
        "yellow": "yellow",
        "blue": "blue",
        "magenta": "magenta",
        "cyan": "cyan",
        "white": "white",
        "lightBlack": "bright_black",
        "lightRed": "bright_red",
        "lightGreen": "bright_green",
        "lightYellow": "bright_yellow",
        "lightBlue": "bright_blue",
        "lightMagenta": "bright_magenta",
        "lightCyan": "bright_cyan",
        "lightWhite": "bright_white",
    }

    @classmethod
    def can_parse(cls, content: str) -> bool:
        """Check if this looks like a Hyper config file."""
        # Look for typical Hyper config patterns
        indicators = [
            "module.exports",
            "fontSize:",
            "fontFamily:",
            "cursorColor:",
            "cursorShape:",
            "updateChannel:",
        ]
        return any(indicator in content for indicator in indicators)

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """Parse a Hyper configuration file into CTEC format."""
        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()

        # Execute the JavaScript to get the config object
        exports = execute_hyper_config(content)
        config = exports.get("config", {})

        ctec = CTEC(source_terminal="hyper")

        # Parse font settings
        font = cls._parse_font(config)
        if font:
            ctec.font = font

        # Parse cursor settings
        cursor = cls._parse_cursor(config)
        if cursor:
            ctec.cursor = cursor

        # Parse window settings
        window = cls._parse_window(config)
        if window:
            ctec.window = window

        # Parse color scheme
        color_scheme = cls._parse_colors(config)
        if color_scheme:
            ctec.color_scheme = color_scheme

        # Parse behavior settings
        behavior = cls._parse_behavior(config)
        if behavior:
            ctec.behavior = behavior

        # Parse scroll settings
        scroll = cls._parse_scroll(config)
        if scroll:
            ctec.scroll = scroll

        # Parse keybindings
        keymaps = exports.get("keymaps", {})
        if keymaps:
            ctec.key_bindings = cls._parse_keybindings(keymaps)

        # Store plugins as terminal-specific settings
        plugins = exports.get("plugins", [])
        if plugins:
            ctec.add_terminal_specific("hyper", "plugins", plugins)

        local_plugins = exports.get("localPlugins", [])
        if local_plugins:
            ctec.add_terminal_specific("hyper", "localPlugins", local_plugins)

        # Store Hyper-specific settings
        cls._parse_terminal_specific(config, ctec)

        return ctec

    @classmethod
    def _parse_font(cls, config: dict) -> FontConfig | None:
        """Parse font configuration from Hyper config."""
        font = FontConfig()
        has_values = False

        if "fontFamily" in config:
            # Hyper fontFamily is a CSS font-family string with fallbacks
            family_str = config["fontFamily"]
            families = [f.strip().strip("\"'") for f in family_str.split(",")]
            if families:
                font.family = families[0]
                if len(families) > 1:
                    font.fallback_fonts = families[1:]
                has_values = True

        if "fontSize" in config:
            font.size = float(config["fontSize"])
            has_values = True

        if "fontWeight" in config:
            weight = config["fontWeight"]
            if weight == "bold":
                font.weight = FontWeight.BOLD
            elif weight == "normal":
                font.weight = FontWeight.REGULAR
            elif isinstance(weight, int):
                # Numeric weight (100-900)
                try:
                    font.weight = FontWeight(weight)
                except ValueError:
                    pass
            has_values = True

        if "fontWeightBold" in config:
            # Store as terminal-specific since CTEC doesn't have separate bold weight
            pass  # Handled in _parse_terminal_specific

        if "lineHeight" in config:
            font.line_height = float(config["lineHeight"])
            has_values = True

        if "letterSpacing" in config:
            # Hyper uses letter-spacing in CSS units
            # Store as terminal-specific since CTEC uses cell_width multiplier
            pass  # Handled in _parse_terminal_specific

        return font if has_values else None

    @classmethod
    def _parse_cursor(cls, config: dict) -> CursorConfig | None:
        """Parse cursor configuration from Hyper config."""
        cursor = CursorConfig()
        has_values = False

        if "cursorShape" in config:
            shape = config["cursorShape"].upper()
            cursor.style = cls.CURSOR_STYLE_MAP.get(shape, CursorStyle.BLOCK)
            has_values = True

        if "cursorBlink" in config:
            cursor.blink = bool(config["cursorBlink"])
            has_values = True

        return cursor if has_values else None

    @classmethod
    def _parse_window(cls, config: dict) -> WindowConfig | None:
        """Parse window configuration from Hyper config."""
        window = WindowConfig()
        has_values = False

        if "windowSize" in config:
            size = config["windowSize"]
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                # windowSize is [width, height] in pixels
                # We can't directly convert to columns/rows without knowing font size
                # Store as terminal-specific
                pass  # Handled in _parse_terminal_specific
            has_values = True

        if "padding" in config:
            # Hyper padding is CSS-style: "12px 14px" or "12px"
            padding_str = config["padding"]
            parts = padding_str.replace("px", "").split()
            if len(parts) == 1:
                window.padding_horizontal = int(parts[0])
                window.padding_vertical = int(parts[0])
            elif len(parts) >= 2:
                window.padding_vertical = int(parts[0])
                window.padding_horizontal = int(parts[1])
            has_values = True

        return window if has_values else None

    @classmethod
    def _parse_colors(cls, config: dict) -> ColorScheme | None:
        """Parse color scheme from Hyper config."""
        scheme = ColorScheme()
        has_values = False

        # Foreground color
        if "foregroundColor" in config:
            rgb = parse_hyper_color(config["foregroundColor"])
            if rgb:
                scheme.foreground = Color(*rgb)
                has_values = True

        # Background color
        if "backgroundColor" in config:
            rgb = parse_hyper_color(config["backgroundColor"])
            if rgb:
                scheme.background = Color(*rgb)
                has_values = True

        # Cursor color
        if "cursorColor" in config:
            rgb = parse_hyper_color(config["cursorColor"])
            if rgb:
                scheme.cursor = Color(*rgb)
                has_values = True

        # Cursor accent color (text under cursor)
        if "cursorAccentColor" in config:
            rgb = parse_hyper_color(config["cursorAccentColor"])
            if rgb:
                scheme.cursor_text = Color(*rgb)
                has_values = True

        # Selection color
        if "selectionColor" in config:
            rgb = parse_hyper_color(config["selectionColor"])
            if rgb:
                scheme.selection = Color(*rgb)
                has_values = True

        # Border color (not directly in CTEC, store as terminal-specific)

        # ANSI colors palette
        colors = config.get("colors", {})
        for hyper_key, ctec_key in cls.ANSI_TO_CTEC_MAP.items():
            if hyper_key in colors:
                rgb = parse_hyper_color(colors[hyper_key])
                if rgb:
                    setattr(scheme, ctec_key, Color(*rgb))
                    has_values = True

        return scheme if has_values else None

    @classmethod
    def _parse_behavior(cls, config: dict) -> BehaviorConfig | None:
        """Parse behavior configuration from Hyper config."""
        behavior = BehaviorConfig()
        has_values = False

        if "shell" in config and config["shell"]:
            behavior.shell = config["shell"]
            has_values = True

        if "shellArgs" in config:
            args = config["shellArgs"]
            if isinstance(args, list):
                behavior.shell_args = args
            has_values = True

        if "env" in config:
            env = config["env"]
            if isinstance(env, dict):
                behavior.environment_variables = env
            has_values = True

        if "copyOnSelect" in config:
            behavior.copy_on_select = bool(config["copyOnSelect"])
            has_values = True

        return behavior if has_values else None

    @classmethod
    def _parse_scroll(cls, config: dict) -> ScrollConfig | None:
        """Parse scroll configuration from Hyper config."""
        if "scrollback" in config:
            lines = int(config["scrollback"])
            return ScrollConfig.from_lines(lines)
        return None

    @classmethod
    def _parse_keybindings(cls, keymaps: dict) -> list[KeyBinding]:
        """Parse keybindings from Hyper keymaps."""
        bindings = []

        for action, key_combo in keymaps.items():
            if not key_combo:
                continue

            # Parse the key combo (e.g., "cmd+alt+o")
            parts = key_combo.lower().split("+")
            key = parts[-1] if parts else ""
            mods = parts[:-1] if len(parts) > 1 else []

            # Normalize modifier names
            mod_map = {
                "cmd": "super",
                "command": "super",
                "ctrl": "ctrl",
                "control": "ctrl",
                "alt": "alt",
                "option": "alt",
                "shift": "shift",
            }
            normalized_mods = [mod_map.get(m, m) for m in mods]

            bindings.append(
                KeyBinding(
                    action=action,
                    key=key,
                    mods=normalized_mods,
                )
            )

        return bindings

    @classmethod
    def _parse_terminal_specific(cls, config: dict, ctec: CTEC) -> None:
        """Store Hyper-specific settings that don't map to CTEC."""
        specific_keys = [
            "updateChannel",
            "fontWeightBold",
            "letterSpacing",
            "uiFontFamily",
            "windowSize",
            "borderColor",
            "css",
            "termCSS",
            "showHamburgerMenu",
            "showWindowControls",
            "quickEdit",
            "macOptionSelectionMode",
            "webGLRenderer",
            "webLinksActivationKey",
            "defaultSSHApp",
            "modifierKeys",
        ]

        for key in specific_keys:
            if key in config and config[key] is not None:
                ctec.add_terminal_specific("hyper", key, config[key])

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """Export CTEC configuration to Hyper .hyper.js format."""
        config_items: list[str] = []

        # Font settings
        if ctec.font:
            cls._export_font(ctec.font, config_items)

        # Cursor settings
        if ctec.cursor:
            cls._export_cursor(ctec.cursor, config_items)

        # Window settings
        if ctec.window:
            cls._export_window(ctec.window, config_items)

        # Color scheme
        if ctec.color_scheme:
            cls._export_colors(ctec.color_scheme, config_items)

        # Behavior settings
        if ctec.behavior:
            cls._export_behavior(ctec.behavior, config_items)

        # Scroll settings
        if ctec.scroll:
            cls._export_scroll(ctec.scroll, config_items)

        # Terminal-specific settings
        cls._export_terminal_specific(ctec, config_items)

        # Keybindings
        keymaps = cls._export_keybindings(ctec.key_bindings)

        # Plugins
        plugins = ctec.get_terminal_specific("hyper", "plugins")
        plugins_str = cls._format_js_array(plugins) if plugins else "[]"

        local_plugins = ctec.get_terminal_specific("hyper", "localPlugins")
        local_plugins_str = (
            cls._format_js_array(local_plugins) if local_plugins else "[]"
        )

        # Build the config object
        config_body = ",\n    ".join(config_items) if config_items else ""

        output = f"""// Hyper configuration
// Generated by Console Cowboy
// See https://hyper.is#cfg for all options

module.exports = {{
  config: {{
    {config_body}
  }},

  plugins: {plugins_str},

  localPlugins: {local_plugins_str},

  keymaps: {keymaps}
}};
"""

        return output

    @classmethod
    def _export_font(cls, font: FontConfig, items: list[str]) -> None:
        """Export font configuration to Hyper format."""
        if font.family:
            # Build font-family string with fallbacks
            families = [font.family]
            if font.fallback_fonts:
                families.extend(font.fallback_fonts)

            if len(families) == 1:
                # Single font - use simple format
                items.append(f"fontFamily: '{families[0]}'")
            else:
                # Multiple fonts - quote names with spaces, use CSS format
                family_str = ", ".join(f'"{f}"' if " " in f else f for f in families)
                items.append(f"fontFamily: '{family_str}'")

        if font.size is not None:
            items.append(f"fontSize: {int(font.size)}")

        if font.weight is not None:
            if font.weight == FontWeight.BOLD:
                items.append("fontWeight: 'bold'")
            elif font.weight == FontWeight.REGULAR:
                items.append("fontWeight: 'normal'")
            else:
                items.append(f"fontWeight: {font.weight.value}")

        if font.line_height is not None:
            items.append(f"lineHeight: {font.line_height}")

    @classmethod
    def _export_cursor(cls, cursor: CursorConfig, items: list[str]) -> None:
        """Export cursor configuration to Hyper format."""
        if cursor.style is not None:
            shape = cls.CURSOR_STYLE_EXPORT_MAP.get(cursor.style, "BLOCK")
            items.append(f"cursorShape: '{shape}'")

        if cursor.blink is not None:
            items.append(f"cursorBlink: {str(cursor.blink).lower()}")

    @classmethod
    def _export_window(cls, window: WindowConfig, items: list[str]) -> None:
        """Export window configuration to Hyper format."""
        if window.padding_horizontal is not None or window.padding_vertical is not None:
            h = window.padding_horizontal or 0
            v = window.padding_vertical or 0
            if h == v:
                items.append(f"padding: '{h}px'")
            else:
                items.append(f"padding: '{v}px {h}px'")

    @classmethod
    def _export_colors(cls, scheme: ColorScheme, items: list[str]) -> None:
        """Export color scheme to Hyper format."""
        if scheme.foreground:
            items.append(f"foregroundColor: '{scheme.foreground.to_hex()}'")

        if scheme.background:
            items.append(f"backgroundColor: '{scheme.background.to_hex()}'")

        if scheme.cursor:
            items.append(f"cursorColor: '{scheme.cursor.to_hex()}'")

        if scheme.cursor_text:
            items.append(f"cursorAccentColor: '{scheme.cursor_text.to_hex()}'")

        if scheme.selection:
            items.append(f"selectionColor: '{scheme.selection.to_hex()}'")

        # ANSI colors
        ansi_colors: dict[str, str] = {}
        ctec_to_ansi = {v: k for k, v in cls.ANSI_TO_CTEC_MAP.items()}

        for ctec_key, hyper_key in ctec_to_ansi.items():
            color = getattr(scheme, ctec_key, None)
            if color:
                ansi_colors[hyper_key] = color.to_hex()

        if ansi_colors:
            colors_items = [f"{k}: '{v}'" for k, v in ansi_colors.items()]
            colors_str = ",\n      ".join(colors_items)
            items.append(f"colors: {{\n      {colors_str}\n    }}")

    @classmethod
    def _export_behavior(cls, behavior: BehaviorConfig, items: list[str]) -> None:
        """Export behavior configuration to Hyper format."""
        if behavior.shell:
            items.append(f"shell: '{behavior.shell}'")

        if behavior.shell_args:
            args_str = ", ".join(f"'{a}'" for a in behavior.shell_args)
            items.append(f"shellArgs: [{args_str}]")

        if behavior.environment_variables:
            env_items = [
                f"{k}: '{v}'" for k, v in behavior.environment_variables.items()
            ]
            env_str = ", ".join(env_items)
            items.append(f"env: {{ {env_str} }}")

        if behavior.copy_on_select is not None:
            items.append(f"copyOnSelect: {str(behavior.copy_on_select).lower()}")

    @classmethod
    def _export_scroll(cls, scroll: ScrollConfig, items: list[str]) -> None:
        """Export scroll configuration to Hyper format."""
        lines = scroll.get_effective_lines(default=1000)
        items.append(f"scrollback: {lines}")

    @classmethod
    def _export_terminal_specific(cls, ctec: CTEC, items: list[str]) -> None:
        """Export terminal-specific settings back to Hyper."""
        for setting in ctec.get_terminal_specific("hyper"):
            # Skip plugins and localPlugins (handled separately)
            if setting.key in ("plugins", "localPlugins"):
                continue

            items.append(f"{setting.key}: {cls._format_js_value(setting.value)}")

    @classmethod
    def _export_keybindings(cls, bindings: list[KeyBinding]) -> str:
        """Export keybindings to Hyper keymaps format."""
        if not bindings:
            return "{}"

        keymap_items = []
        for binding in bindings:
            # Reverse normalize modifiers
            mod_map = {
                "super": "cmd",
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
            }
            mods = [mod_map.get(m, m) for m in binding.mods]
            key_combo = "+".join(mods + [binding.key])
            keymap_items.append(f"'{binding.action}': '{key_combo}'")

        keymaps_str = ",\n    ".join(keymap_items)
        return f"{{\n    {keymaps_str}\n  }}"

    @classmethod
    def _format_js_value(cls, value: Any) -> str:
        """Format a Python value as JavaScript."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return cls._format_js_array(value)
        elif isinstance(value, dict):
            items = [f"{k}: {cls._format_js_value(v)}" for k, v in value.items()]
            return "{ " + ", ".join(items) + " }"
        else:
            return f"'{value}'"

    @classmethod
    def _format_js_array(cls, arr: list | Any) -> str:
        """Format a Python list as JavaScript array."""
        if not isinstance(arr, list):
            return "[]"
        items = [cls._format_js_value(item) for item in arr]
        return "[" + ", ".join(items) + "]"
