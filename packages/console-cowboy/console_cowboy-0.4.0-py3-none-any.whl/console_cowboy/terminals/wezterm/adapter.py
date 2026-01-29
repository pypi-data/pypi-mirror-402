"""
Wezterm configuration adapter.

Wezterm uses Lua for configuration, stored in ~/.wezterm.lua or
~/.config/wezterm/wezterm.lua

This adapter uses a Lua interpreter with a mock wezterm module to
accurately parse WezTerm configurations.
"""

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
    KeyBindingScope,
    PaneConfig,
    ScrollConfig,
    TabBarPosition,
    TabBarStyle,
    TabBarVisibility,
    TabConfig,
    TerminalSpecificSetting,
    TextHintAction,
    TextHintConfig,
    TextHintRule,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color
from console_cowboy.utils.fonts import is_postscript_name, postscript_to_friendly

from ..base import TerminalAdapter
from .lua import ActionSpec, EventCallback, FontSpec, execute_wezterm_config

# Mapping of WezTerm action names to their parameter format
# Format: action_name -> (param_name, is_table)
# is_table=True means the param should be wrapped as { param_name = value }
# is_table=False means it's a simple function call action(value)
ACTION_PARAM_FORMATS = {
    # Clipboard actions - simple string parameter
    "CopyTo": ("destination", False),
    "PasteFrom": ("source", False),
    # Tab actions
    "SpawnTab": ("domain", False),
    "ActivateTab": ("tab_index", False),
    "ActivateTabRelative": ("offset", False),
    # Pane actions - table parameters
    "SplitHorizontal": ("domain", True),
    "SplitVertical": ("domain", True),
    "SplitPane": ("direction", True),
    "ActivatePaneDirection": ("direction", False),
    "AdjustPaneSize": ("direction", False),
    # Scroll actions
    "ScrollByPage": ("amount", False),
    "ScrollByLine": ("amount", False),
    "ScrollToPrompt": ("direction", False),
    # Font size
    "IncreaseFontSize": (None, False),
    "DecreaseFontSize": (None, False),
    "ResetFontSize": (None, False),
    # Search
    "Search": ("pattern", True),
    # Key table activation
    "ActivateKeyTable": ("name", True),
    "PopKeyTable": (None, False),
    # Window actions
    "SpawnWindow": (None, False),
    "ToggleFullScreen": (None, False),
    "Hide": (None, False),
    "Show": (None, False),
    "CloseCurrentTab": ("confirm", True),
    "CloseCurrentPane": ("confirm", True),
    # Quick select
    "QuickSelect": (None, False),
    "QuickSelectArgs": ("patterns", True),
    # Input
    "SendString": ("text", False),
    "SendKey": ("key", True),
    # Multiple actions
    "Multiple": ("actions", False),
}


class WeztermAdapter(TerminalAdapter):
    """
    Adapter for Wezterm terminal emulator.

    Uses a Lua interpreter with a mock wezterm module to accurately
    parse WezTerm configurations.
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
    def can_parse(cls, content: str) -> bool:
        """Check if content looks like a Wezterm Lua config."""
        # Wezterm uses Lua with specific patterns
        wezterm_markers = [
            "local wezterm",
            "require 'wezterm'",
            'require "wezterm"',
            "require('wezterm')",
            'require("wezterm")',
            "wezterm.config_builder",
            "config.font",
            "config.colors",
            "config.font_size",
            "wezterm.font",
            "wezterm.font_with_fallback",
        ]
        for marker in wezterm_markers:
            if marker in content:
                return True
        return False

    @classmethod
    def _parse_lua_color(cls, color_str: str) -> Optional["Color"]:
        """Parse a color from Lua format."""
        if color_str is None:
            return None
        color_str = str(color_str).strip().strip("'\"")
        if color_str.lower() == "none":
            return None
        try:
            return normalize_color(color_str)
        except ValueError:
            return None

    @classmethod
    def _parse_colors_dict(cls, colors: dict) -> ColorScheme:
        """Parse a colors dict into a ColorScheme."""
        scheme = ColorScheme()

        # Parse simple color assignments
        color_mappings = {
            "foreground": "foreground",
            "background": "background",
            "cursor_fg": "cursor_text",
            "cursor_bg": "cursor",
            "selection_fg": "selection_text",
            "selection_bg": "selection",
        }

        for wez_key, ctec_key in color_mappings.items():
            if wez_key in colors:
                color = cls._parse_lua_color(colors[wez_key])
                if color:
                    setattr(scheme, ctec_key, color)

        # Parse ANSI colors array
        if "ansi" in colors:
            ansi_colors = colors["ansi"]
            if isinstance(ansi_colors, (list, tuple)):
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
                for name, color_str in zip(ansi_names, ansi_colors, strict=False):
                    color = cls._parse_lua_color(color_str)
                    if color:
                        setattr(scheme, name, color)

        # Parse bright colors array
        if "brights" in colors:
            bright_colors = colors["brights"]
            if isinstance(bright_colors, (list, tuple)):
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
                for name, color_str in zip(bright_names, bright_colors, strict=False):
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
        """Parse a Wezterm configuration file using Lua execution."""
        ctec = CTEC(source_terminal="wezterm")

        if content is None:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            content = path.read_text()

        # Execute the Lua config with our mock wezterm module
        try:
            config = execute_wezterm_config(content)
        except ValueError as e:
            ctec.add_warning(f"Failed to execute Lua config: {e}")
            return ctec

        # Parse color_scheme (named scheme) - takes precedence if no custom colors
        if "color_scheme" in config:
            scheme_name = str(config["color_scheme"]).strip("'\"")
            if not ctec.color_scheme:
                ctec.color_scheme = ColorScheme()
            ctec.color_scheme.name = scheme_name

        # Parse custom colors (may override or supplement named scheme)
        if "colors" in config:
            colors = config["colors"]
            if isinstance(colors, dict):
                parsed_scheme = cls._parse_colors_dict(colors)
                if ctec.color_scheme and ctec.color_scheme.name:
                    # Merge custom colors with named scheme
                    for attr in dir(parsed_scheme):
                        if not attr.startswith("_") and attr not in (
                            "name",
                            "author",
                            "variant",
                        ):
                            val = getattr(parsed_scheme, attr)
                            if val is not None:
                                setattr(ctec.color_scheme, attr, val)
                else:
                    ctec.color_scheme = parsed_scheme

        # Parse font
        font = FontConfig()
        if "font" in config:
            font_val = config["font"]
            if isinstance(font_val, FontSpec):
                font.family = font_val.family
                if font_val.weight:
                    try:
                        font.weight = FontWeight.from_string(font_val.weight)
                    except (ValueError, KeyError):
                        ctec.add_warning(f"Unknown font weight: {font_val.weight}")
                if font_val.fallbacks:
                    font.fallback_fonts = font_val.fallbacks
                # Handle HarfBuzz features -> ligatures
                if font_val.harfbuzz_features:
                    for feature in font_val.harfbuzz_features:
                        if feature in ("liga=0", "clig=0", "calt=0"):
                            font.ligatures = False
                            break
                    # Store full harfbuzz features as terminal-specific for round-trip
                    ctec.terminal_specific.append(
                        TerminalSpecificSetting(
                            terminal="wezterm",
                            key="font_harfbuzz_features",
                            value=font_val.harfbuzz_features,
                        )
                    )
                # Store FreeType settings as terminal-specific
                if font_val.freetype_load_target:
                    ctec.terminal_specific.append(
                        TerminalSpecificSetting(
                            terminal="wezterm",
                            key="font_freetype_load_target",
                            value=font_val.freetype_load_target,
                        )
                    )

        if "font_size" in config:
            try:
                font.size = float(config["font_size"])
            except (ValueError, TypeError):
                ctec.add_warning(f"Invalid font_size: {config['font_size']}")

        if "line_height" in config:
            try:
                font.line_height = float(config["line_height"])
            except (ValueError, TypeError):
                ctec.add_warning(f"Invalid line_height: {config['line_height']}")

        if font.family or font.size:
            ctec.font = font

        # Parse cursor
        cursor = CursorConfig()
        if "default_cursor_style" in config:
            cursor_style = str(config["default_cursor_style"]).strip("'\"")
            if cursor_style in cls.CURSOR_STYLE_MAP:
                cursor.style = cls.CURSOR_STYLE_MAP[cursor_style]
                cursor.blink = "Blinking" in cursor_style

        if "cursor_blink_rate" in config:
            try:
                rate = int(config["cursor_blink_rate"])
                cursor.blink = rate > 0
                if rate > 0:
                    cursor.blink_interval = rate
            except (ValueError, TypeError):
                pass

        if cursor.style or cursor.blink is not None:
            ctec.cursor = cursor

        # Parse window
        window = WindowConfig()

        if "initial_cols" in config:
            try:
                window.columns = int(config["initial_cols"])
            except (ValueError, TypeError):
                pass

        if "initial_rows" in config:
            try:
                window.rows = int(config["initial_rows"])
            except (ValueError, TypeError):
                pass

        if "window_background_opacity" in config:
            try:
                window.opacity = float(config["window_background_opacity"])
            except (ValueError, TypeError):
                pass

        if "macos_window_background_blur" in config:
            try:
                window.blur = int(config["macos_window_background_blur"])
            except (ValueError, TypeError):
                pass

        if "window_padding" in config:
            padding = config["window_padding"]
            if isinstance(padding, dict):
                if "left" in padding:
                    try:
                        window.padding_horizontal = int(padding["left"])
                    except (ValueError, TypeError):
                        pass
                if "top" in padding:
                    try:
                        window.padding_vertical = int(padding["top"])
                    except (ValueError, TypeError):
                        pass

        if "window_decorations" in config:
            decorations = str(config["window_decorations"]).strip("'\"")
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

        if "default_prog" in config:
            default_prog = config["default_prog"]
            if isinstance(default_prog, (list, tuple)) and len(default_prog) > 0:
                behavior.shell = str(default_prog[0])
                if len(default_prog) > 1:
                    behavior.shell_args = [str(arg) for arg in default_prog[1:]]
            elif isinstance(default_prog, dict):
                # Lua table with numeric keys (1-indexed in Lua)
                if 1 in default_prog:
                    behavior.shell = str(default_prog[1])
                    # Get remaining args (keys 2, 3, ...)
                    args = []
                    i = 2
                    while i in default_prog:
                        args.append(str(default_prog[i]))
                        i += 1
                    if args:
                        behavior.shell_args = args

        # Parse environment variables
        if "set_environment_variables" in config:
            env_vars = config["set_environment_variables"]
            if isinstance(env_vars, dict):
                behavior.environment_variables = {
                    str(k): str(v) for k, v in env_vars.items()
                }

        if "scrollback_lines" in config:
            try:
                lines = int(config["scrollback_lines"])
                ctec.scroll = ScrollConfig.from_lines(lines)
            except (ValueError, TypeError):
                ctec.add_warning(
                    f"Invalid scrollback_lines: {config['scrollback_lines']}"
                )

        if "audible_bell" in config:
            audible_bell = str(config["audible_bell"]).strip("'\"")
            if audible_bell == "Disabled":
                behavior.bell_mode = BellMode.NONE
            else:
                behavior.bell_mode = BellMode.AUDIBLE

        if "visual_bell" in config:
            visual_bell = config["visual_bell"]
            if isinstance(visual_bell, dict):
                duration = visual_bell.get("fade_in_duration_ms") or visual_bell.get(
                    "duration_ms"
                )
                if duration and int(duration) > 0:
                    behavior.bell_mode = BellMode.VISUAL

        if (
            behavior.shell
            or behavior.scrollback_lines
            or behavior.bell_mode
            or behavior.environment_variables
        ):
            ctec.behavior = behavior

        # Parse tab settings
        tabs = TabConfig()
        if "enable_tab_bar" in config:
            enable_tab_bar = config["enable_tab_bar"]
            if isinstance(enable_tab_bar, bool) and not enable_tab_bar:
                tabs.visibility = TabBarVisibility.NEVER
            elif str(enable_tab_bar).lower() == "false":
                tabs.visibility = TabBarVisibility.NEVER

        if "tab_bar_at_bottom" in config:
            tab_bar_at_bottom = config["tab_bar_at_bottom"]
            if isinstance(tab_bar_at_bottom, bool):
                tabs.position = (
                    TabBarPosition.BOTTOM if tab_bar_at_bottom else TabBarPosition.TOP
                )
            elif str(tab_bar_at_bottom).lower() == "true":
                tabs.position = TabBarPosition.BOTTOM
            else:
                tabs.position = TabBarPosition.TOP

        if "use_fancy_tab_bar" in config:
            use_fancy = config["use_fancy_tab_bar"]
            if isinstance(use_fancy, bool):
                tabs.style = TabBarStyle.FANCY if use_fancy else TabBarStyle.NATIVE
            elif str(use_fancy).lower() == "true":
                tabs.style = TabBarStyle.FANCY
            else:
                tabs.style = TabBarStyle.NATIVE

        if "hide_tab_bar_if_only_one_tab" in config:
            hide_single = config["hide_tab_bar_if_only_one_tab"]
            if isinstance(hide_single, bool):
                tabs.auto_hide_single = hide_single
            elif str(hide_single).lower() == "true":
                tabs.auto_hide_single = True

        if "tab_max_width" in config:
            try:
                tabs.max_width = int(config["tab_max_width"])
            except (ValueError, TypeError):
                pass

        if "show_tab_index_in_tab_bar" in config:
            show_index = config["show_tab_index_in_tab_bar"]
            if isinstance(show_index, bool):
                tabs.show_index = show_index
            elif str(show_index).lower() == "true":
                tabs.show_index = True

        # Parse tab colors from colors.tab_bar
        if "colors" in config:
            colors = config["colors"]
            if isinstance(colors, dict):
                if "tab_bar" in colors:
                    tab_bar = colors["tab_bar"]
                    if isinstance(tab_bar, dict):
                        if "background" in tab_bar:
                            tabs.bar_background = cls._parse_lua_color(
                                tab_bar["background"]
                            )
                        if "active_tab" in tab_bar:
                            active_tab = tab_bar["active_tab"]
                            if isinstance(active_tab, dict):
                                if "bg_color" in active_tab:
                                    tabs.active_background = cls._parse_lua_color(
                                        active_tab["bg_color"]
                                    )
                                if "fg_color" in active_tab:
                                    tabs.active_foreground = cls._parse_lua_color(
                                        active_tab["fg_color"]
                                    )
                        if "inactive_tab" in tab_bar:
                            inactive_tab = tab_bar["inactive_tab"]
                            if isinstance(inactive_tab, dict):
                                if "bg_color" in inactive_tab:
                                    tabs.inactive_background = cls._parse_lua_color(
                                        inactive_tab["bg_color"]
                                    )
                                if "fg_color" in inactive_tab:
                                    tabs.inactive_foreground = cls._parse_lua_color(
                                        inactive_tab["fg_color"]
                                    )

        # Add tabs if any tab settings were configured
        if any(
            getattr(tabs, f) is not None
            for f in [
                "visibility",
                "position",
                "style",
                "auto_hide_single",
                "max_width",
                "show_index",
                "active_foreground",
                "active_background",
                "inactive_foreground",
                "inactive_background",
                "bar_background",
            ]
        ):
            ctec.tabs = tabs

        # Parse pane settings
        panes = PaneConfig()
        if "inactive_pane_hsb" in config:
            hsb = config["inactive_pane_hsb"]
            if isinstance(hsb, dict) and "brightness" in hsb:
                try:
                    panes.inactive_dim_factor = float(hsb["brightness"])
                except (ValueError, TypeError):
                    pass

        if "pane_focus_follows_mouse" in config:
            focus_follows = config["pane_focus_follows_mouse"]
            if isinstance(focus_follows, bool):
                panes.focus_follows_mouse = focus_follows
            elif str(focus_follows).lower() == "true":
                panes.focus_follows_mouse = True

        # Check for divider color from colors.split parsed above
        if "colors" in config and isinstance(config["colors"], dict):
            if "split" in config["colors"]:
                panes.divider_color = cls._parse_lua_color(config["colors"]["split"])

        # Add panes if any pane settings were configured
        if any(
            getattr(panes, f) is not None
            for f in [
                "inactive_dim_factor",
                "divider_color",
                "focus_follows_mouse",
            ]
        ):
            ctec.panes = panes

        # Parse leader key
        if "leader" in config:
            leader = config["leader"]
            if isinstance(leader, dict):
                leader_key = leader.get("key")
                leader_mods = leader.get("mods", "")
                leader_timeout = leader.get("timeout_milliseconds", 1000)
                if leader_key:
                    ctec.terminal_specific.append(
                        TerminalSpecificSetting(
                            terminal="wezterm",
                            key="leader",
                            value={
                                "key": leader_key,
                                "mods": leader_mods,
                                "timeout_milliseconds": leader_timeout,
                            },
                        )
                    )

        # Parse key_tables (for round-trip preservation)
        if "key_tables" in config:
            key_tables = config["key_tables"]
            if isinstance(key_tables, dict):
                # Store the raw key_tables for round-trip
                ctec.terminal_specific.append(
                    TerminalSpecificSetting(
                        terminal="wezterm",
                        key="key_tables",
                        value=key_tables,
                    )
                )

        # Parse key bindings
        if "keys" in config:
            keys = config["keys"]
            if isinstance(keys, (list, dict)):
                # Convert dict with numeric keys to list
                if isinstance(keys, dict):
                    keys = [keys[i] for i in sorted(keys.keys()) if isinstance(i, int)]

                for binding in keys:
                    if isinstance(binding, dict):
                        key = binding.get("key")
                        mods = binding.get("mods", "")
                        action = binding.get("action")

                        if key and action:
                            # Parse modifiers
                            mod_list = []
                            if mods:
                                mod_list = [m.strip() for m in str(mods).split("|")]

                            # Check for LEADER modifier
                            has_leader = "LEADER" in mod_list
                            if has_leader:
                                mod_list = [m for m in mod_list if m != "LEADER"]

                            # Parse action
                            action_name = None
                            action_param = None
                            if isinstance(action, ActionSpec):
                                action_name = action.name
                                if action.args:
                                    # Handle different argument types
                                    arg = action.args[0]
                                    if isinstance(arg, dict):
                                        # Table argument - store as JSON-like string
                                        action_param = str(arg)
                                    else:
                                        action_param = str(arg)
                            elif isinstance(action, str):
                                action_name = action

                            if action_name:
                                kb = KeyBinding(
                                    action=action_name,
                                    key=str(key),
                                    mods=mod_list,
                                    action_param=action_param,
                                )
                                # Store leader info in key_sequence for conceptual mapping
                                if has_leader:
                                    # Mark this as a leader-based binding
                                    kb.key_sequence = ["LEADER"]
                                ctec.key_bindings.append(kb)

        # Parse hyperlink_rules
        if "hyperlink_rules" in config:
            rules = config["hyperlink_rules"]
            if isinstance(rules, (list, dict)):
                # Convert dict with numeric keys to list
                if isinstance(rules, dict):
                    rules = [
                        rules[i] for i in sorted(rules.keys()) if isinstance(i, int)
                    ]

                hints = TextHintConfig(enabled=True)
                for rule in rules:
                    if isinstance(rule, dict):
                        regex = rule.get("regex")
                        url_format = rule.get("format")
                        if regex:
                            hint_rule = TextHintRule(
                                regex=str(regex),
                                action=TextHintAction.OPEN,
                                parameter=str(url_format) if url_format else None,
                            )
                            # Detect if it's a URL pattern
                            if url_format and (
                                "http" in str(url_format).lower()
                                or "mailto" in str(url_format).lower()
                            ):
                                hint_rule.hyperlinks = True
                            hints.rules.append(hint_rule)

                if hints.rules:
                    ctec.text_hints = hints

        # Capture wezterm.on() event callbacks (for round-trip warning)
        if "_wezterm_events" in config:
            events = config["_wezterm_events"]
            if events:
                event_names = [
                    e.event_name for e in events if isinstance(e, EventCallback)
                ]
                if event_names:
                    ctec.add_warning(
                        f"WezTerm event callbacks ({', '.join(event_names)}) cannot be "
                        "translated to other terminals. These will be lost during conversion."
                    )
                    # Store event names for potential round-trip
                    ctec.terminal_specific.append(
                        TerminalSpecificSetting(
                            terminal="wezterm",
                            key="event_callbacks",
                            value=event_names,
                        )
                    )

        return ctec

    @classmethod
    def _format_action(cls, action: str, param: str | None) -> str:
        """Format a WezTerm action with proper Lua syntax."""
        if param is None:
            return f"wezterm.action.{action}"

        # Check if we have special formatting for this action
        if action in ACTION_PARAM_FORMATS:
            param_name, is_table = ACTION_PARAM_FORMATS[action]
            if param_name is None:
                # No parameter needed
                return f"wezterm.action.{action}"
            elif is_table:
                # Table parameter: action { param_name = value }
                return f'wezterm.action.{action} {{ {param_name} = "{param}" }}'
            else:
                # Simple function call: action(value)
                return f'wezterm.action.{action}("{param}")'

        # Default: simple function call
        return f'wezterm.action.{action}("{param}")'

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

        # Export color_scheme by name (if available)
        if ctec.color_scheme and ctec.color_scheme.name:
            lines.append("-- Color scheme")
            lines.append(f'config.color_scheme = "{ctec.color_scheme.name}"')
            lines.append("")

        # Export custom colors (if any colors are set beyond just the name)
        if ctec.color_scheme:
            scheme = ctec.color_scheme
            has_custom_colors = any(
                [
                    scheme.foreground,
                    scheme.background,
                    scheme.cursor,
                    scheme.cursor_text,
                    scheme.selection,
                    scheme.selection_text,
                    scheme.black,
                    scheme.red,
                ]
            )

            if has_custom_colors:
                lines.append("-- Custom colors")
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
                    lines.append(
                        f'  selection_fg = "{scheme.selection_text.to_hex()}",'
                    )

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

                # Check for HarfBuzz features to restore
                harfbuzz_features = None
                freetype_load_target = None
                for setting in ctec.get_terminal_specific("wezterm"):
                    if setting.key == "font_harfbuzz_features":
                        harfbuzz_features = setting.value
                    elif setting.key == "font_freetype_load_target":
                        freetype_load_target = setting.value

                # If ligatures is explicitly false and no stored features, add liga=0
                if ctec.font.ligatures is False and not harfbuzz_features:
                    harfbuzz_features = ["liga=0", "clig=0", "calt=0"]

                # Build font options
                font_opts = []
                if ctec.font.weight:
                    font_opts.append(f'weight = "{ctec.font.weight.to_string()}"')
                if harfbuzz_features:
                    features_str = ", ".join(f'"{f}"' for f in harfbuzz_features)
                    font_opts.append(f"harfbuzz_features = {{ {features_str} }}")
                if freetype_load_target:
                    font_opts.append(f'freetype_load_target = "{freetype_load_target}"')

                # Determine if we need fallback fonts
                if ctec.font.fallback_fonts:
                    # WezTerm font_with_fallback
                    if font_opts:
                        opts_str = ", ".join(font_opts)
                        primary = f'{{ family = "{font_family}", {opts_str} }}'
                    else:
                        primary = f'"{font_family}"'
                    fallbacks_str = ", ".join(
                        f'"{f}"' for f in ctec.font.fallback_fonts
                    )
                    lines.append(
                        f"config.font = wezterm.font_with_fallback({{ {primary}, {fallbacks_str} }})"
                    )
                elif font_opts:
                    # Use font with options
                    opts_str = ", ".join(font_opts)
                    lines.append(
                        f'config.font = wezterm.font("{font_family}", {{ {opts_str} }})'
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
                    "-- Note: macos_window_background_blur only works on macOS"
                )
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
            if ctec.behavior.shell or ctec.behavior.shell_args:
                prog_parts = []
                if ctec.behavior.shell:
                    prog_parts.append(f'"{ctec.behavior.shell}"')
                if ctec.behavior.shell_args:
                    prog_parts.extend(f'"{arg}"' for arg in ctec.behavior.shell_args)
                if prog_parts:
                    prog_str = ", ".join(prog_parts)
                    lines.append(f"config.default_prog = {{ {prog_str} }}")
            if ctec.behavior.environment_variables:
                lines.append("config.set_environment_variables = {")
                for env_key, env_value in ctec.behavior.environment_variables.items():
                    lines.append(f'  {env_key} = "{env_value}",')
                lines.append("}")
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

        # Export tab settings
        if ctec.tabs:
            lines.append("-- Tab Bar")
            if ctec.tabs.visibility == TabBarVisibility.NEVER:
                lines.append("config.enable_tab_bar = false")
            else:
                lines.append("config.enable_tab_bar = true")
            if ctec.tabs.position is not None:
                if ctec.tabs.position == TabBarPosition.BOTTOM:
                    lines.append("config.tab_bar_at_bottom = true")
                else:
                    lines.append("config.tab_bar_at_bottom = false")
            if ctec.tabs.style is not None:
                if ctec.tabs.style == TabBarStyle.FANCY:
                    lines.append("config.use_fancy_tab_bar = true")
                elif ctec.tabs.style == TabBarStyle.NATIVE:
                    lines.append("config.use_fancy_tab_bar = false")
                else:
                    ctec.add_warning(
                        f"WezTerm only supports native/fancy tab styles. "
                        f"Style '{ctec.tabs.style.value}' will be exported as native."
                    )
                    lines.append("config.use_fancy_tab_bar = false")
            if ctec.tabs.auto_hide_single is not None:
                val = "true" if ctec.tabs.auto_hide_single else "false"
                lines.append(f"config.hide_tab_bar_if_only_one_tab = {val}")
            if ctec.tabs.max_width is not None:
                lines.append(f"config.tab_max_width = {ctec.tabs.max_width}")
            if ctec.tabs.show_index is not None:
                val = "true" if ctec.tabs.show_index else "false"
                lines.append(f"config.show_tab_index_in_tab_bar = {val}")
            lines.append("")

            # Tab colors need to be added to config.colors
            has_tab_colors = any(
                getattr(ctec.tabs, f) is not None
                for f in [
                    "active_foreground",
                    "active_background",
                    "inactive_foreground",
                    "inactive_background",
                    "bar_background",
                ]
            )
            if has_tab_colors:
                lines.append("-- Tab colors")
                lines.append("config.colors = config.colors or {}")
                lines.append("config.colors.tab_bar = {")
                if ctec.tabs.bar_background is not None:
                    lines.append(
                        f'  background = "{ctec.tabs.bar_background.to_hex()}",'
                    )
                if (
                    ctec.tabs.active_foreground is not None
                    or ctec.tabs.active_background is not None
                ):
                    lines.append("  active_tab = {")
                    if ctec.tabs.active_foreground is not None:
                        lines.append(
                            f'    fg_color = "{ctec.tabs.active_foreground.to_hex()}",'
                        )
                    if ctec.tabs.active_background is not None:
                        lines.append(
                            f'    bg_color = "{ctec.tabs.active_background.to_hex()}",'
                        )
                    lines.append("  },")
                if (
                    ctec.tabs.inactive_foreground is not None
                    or ctec.tabs.inactive_background is not None
                ):
                    lines.append("  inactive_tab = {")
                    if ctec.tabs.inactive_foreground is not None:
                        lines.append(
                            f'    fg_color = "{ctec.tabs.inactive_foreground.to_hex()}",'
                        )
                    if ctec.tabs.inactive_background is not None:
                        lines.append(
                            f'    bg_color = "{ctec.tabs.inactive_background.to_hex()}",'
                        )
                    lines.append("  },")
                lines.append("}")
                lines.append("")

            # Warn about unsupported tab features
            unsupported = []
            if ctec.tabs.new_tab_position is not None:
                unsupported.append("new_tab_position")
            if ctec.tabs.inherit_working_directory is not None:
                unsupported.append("inherit_working_directory")
            if unsupported:
                ctec.add_warning(
                    f"WezTerm does not support: {', '.join(unsupported)}. "
                    "These tab settings will not be exported."
                )

        # Export pane settings
        if ctec.panes:
            lines.append("-- Pane Settings")
            if ctec.panes.inactive_dim_factor is not None:
                lines.append("config.inactive_pane_hsb = {")
                lines.append("  saturation = 1.0,")
                lines.append("  hue = 1.0,")
                lines.append(f"  brightness = {ctec.panes.inactive_dim_factor},")
                lines.append("}")
            if ctec.panes.focus_follows_mouse is not None:
                val = "true" if ctec.panes.focus_follows_mouse else "false"
                lines.append(f"config.pane_focus_follows_mouse = {val}")
            if ctec.panes.divider_color is not None:
                lines.append("config.colors = config.colors or {}")
                lines.append(
                    f'config.colors.split = "{ctec.panes.divider_color.to_hex()}"'
                )
            lines.append("")

            # Warn about unsupported pane features
            unsupported = []
            if ctec.panes.inactive_dim_color is not None:
                unsupported.append("inactive_dim_color")
            if unsupported:
                ctec.add_warning(
                    f"WezTerm does not support: {', '.join(unsupported)}. "
                    "These pane settings will not be exported."
                )

        # Export leader key (from terminal-specific settings)
        leader_setting = None
        key_tables_setting = None
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key == "leader":
                leader_setting = setting.value
            elif setting.key == "key_tables":
                key_tables_setting = setting.value

        if leader_setting:
            lines.append("-- Leader key")
            leader_key = leader_setting.get("key", "Space")
            leader_mods = leader_setting.get("mods", "CTRL|SHIFT")
            leader_timeout = leader_setting.get("timeout_milliseconds", 1000)
            lines.append(
                f'config.leader = {{ key = "{leader_key}", mods = "{leader_mods}", timeout_milliseconds = {leader_timeout} }}'
            )
            lines.append("")

        # Export key bindings
        if ctec.key_bindings:
            lines.append("-- Key bindings")
            lines.append("config.keys = {")
            for kb in ctec.key_bindings:
                # Check for unsupported features and warn
                if kb.key_sequence and kb.key_sequence != ["LEADER"]:
                    ctec.add_warning(
                        f"Keybinding with key sequence '{'>'.join(kb.key_sequence)}' cannot be "
                        "directly exported to WezTerm. Consider using WezTerm's key_tables and "
                        "LEADER modifier for similar functionality."
                    )
                    continue
                if kb.scope and kb.scope != KeyBindingScope.APPLICATION:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has scope '{kb.scope.value}' which is not supported "
                        "in WezTerm. It will be exported as a regular (application-scoped) binding."
                    )
                if kb.mode:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has mode restriction '{kb.mode}' which is not "
                        "supported in WezTerm. It will be exported without mode restrictions."
                    )

                # Build modifiers
                mod_list = [m.upper() for m in kb.mods] if kb.mods else []

                # Add LEADER if this was a leader-based binding
                if kb.key_sequence == ["LEADER"]:
                    mod_list.append("LEADER")

                mods = "|".join(mod_list) if mod_list else "NONE"

                # Format action with proper syntax
                action_str = cls._format_action(kb.action, kb.action_param)

                lines.append(
                    f'  {{ key = "{kb.key}", mods = "{mods}", action = {action_str} }},'
                )
            lines.append("}")
            lines.append("")

        # Export key_tables (from terminal-specific settings)
        if key_tables_setting:
            lines.append("-- Key tables")
            lines.append("config.key_tables = {")
            for table_name, bindings in key_tables_setting.items():
                lines.append(f"  {table_name} = {{")
                if isinstance(bindings, (list, dict)):
                    if isinstance(bindings, dict):
                        bindings = list(bindings.values())
                    for binding in bindings:
                        if isinstance(binding, dict):
                            key = binding.get("key", "")
                            action = binding.get("action", "")
                            if isinstance(action, ActionSpec):
                                action_str = cls._format_action(
                                    action.name,
                                    str(action.args[0]) if action.args else None,
                                )
                            elif isinstance(action, str):
                                action_str = f'"{action}"'
                            else:
                                action_str = str(action)
                            lines.append(
                                f'    {{ key = "{key}", action = {action_str} }},'
                            )
                lines.append("  },")
            lines.append("}")
            lines.append("")

        # Restore other terminal-specific settings
        other_settings = []
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key not in (
                "leader",
                "key_tables",
                "font_harfbuzz_features",
                "font_freetype_load_target",
                "event_callbacks",
            ):
                other_settings.append(setting)

        if other_settings:
            lines.append("-- Terminal-specific settings")
            for setting in other_settings:
                value = setting.value
                if isinstance(value, str):
                    value = f'"{value}"'
                elif isinstance(value, bool):
                    value = str(value).lower()
                lines.append(f"config.{setting.key} = {value}")
            lines.append("")

        # Export text hints as hyperlink_rules
        if ctec.text_hints and ctec.text_hints.rules:
            # Filter rules that can be converted to hyperlink_rules
            # WezTerm hyperlink_rules require a URL format, so only OPEN/OPEN_URL actions work
            exportable_rules = []
            non_exportable_count = 0

            for rule in ctec.text_hints.rules:
                if rule.regex:
                    # Check if this rule can be expressed as a hyperlink
                    if (
                        rule.action
                        in (
                            TextHintAction.OPEN,
                            TextHintAction.OPEN_URL,
                            TextHintAction.OPEN_FILE,
                            None,
                        )
                        or rule.hyperlinks
                    ):
                        exportable_rules.append(rule)
                    else:
                        non_exportable_count += 1

            if exportable_rules:
                lines.append("-- Hyperlink rules (from text hints)")
                lines.append(
                    "config.hyperlink_rules = wezterm.default_hyperlink_rules()"
                )
                lines.append("")
                for rule in exportable_rules:
                    # Determine the format string
                    if rule.parameter:
                        # Use stored format from WezTerm round-trip
                        url_format = rule.parameter
                    elif rule.command:
                        # Use command as format if it looks like a URL
                        url_format = rule.command
                    else:
                        # Default: use the full match as URL
                        url_format = "$0"

                    # Escape the regex for Lua bracket notation
                    lua_regex = rule.regex.replace("\\", "\\\\")
                    lines.append("table.insert(config.hyperlink_rules, {")
                    lines.append(f"  regex = [[{lua_regex}]],")
                    lines.append(f'  format = "{url_format}",')
                    lines.append("})")
                lines.append("")

            if non_exportable_count > 0:
                ctec.add_warning(
                    f"WezTerm hyperlink_rules only support URL actions. "
                    f"{non_exportable_count} rule(s) with Copy/Paste/other actions "
                    "could not be exported."
                )

        lines.append("return config")
        return "\n".join(lines)
