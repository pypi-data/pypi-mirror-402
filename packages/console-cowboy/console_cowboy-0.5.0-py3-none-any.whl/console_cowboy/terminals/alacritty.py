"""
Alacritty configuration adapter.

Alacritty uses YAML (versions < 0.13) or TOML (versions >= 0.13) format stored in
~/.config/alacritty/alacritty.yml or ~/.config/alacritty/alacritty.toml
"""

from pathlib import Path

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
    KeyBindingScope,
    ScrollConfig,
    TextHintAction,
    TextHintBinding,
    TextHintConfig,
    TextHintMouseBinding,
    TextHintRule,
    WindowConfig,
)
from console_cowboy.utils.colors import normalize_color

from .base import TerminalAdapter
from .mixins import CursorStyleMixin, ParsingMixin


class AlacrittyAdapter(TerminalAdapter, CursorStyleMixin, ParsingMixin):
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

    # Alacritty hint action mapping to CTEC
    HINT_ACTION_MAP = {
        "Copy": TextHintAction.COPY,
        "Paste": TextHintAction.PASTE,
        "Select": TextHintAction.SELECT,
        "MoveViModeCursor": TextHintAction.MOVE_VI_CURSOR,
    }

    HINT_ACTION_REVERSE_MAP = {v: k for k, v in HINT_ACTION_MAP.items()}

    # Window mapping
    WINDOW_MAPPING = {
        "window.dimensions.columns": ("columns", int),
        "window.dimensions.lines": ("rows", int),
        "window.opacity": ("opacity", float),
        "window.padding.x": ("padding_horizontal", int),
        "window.padding.y": ("padding_vertical", int),
        "window.dynamic_title": ("dynamic_title", bool),
        "window.startup_mode": ("startup_mode", lambda v: v.lower()),
        "window.decorations": (
            "decorations",
            lambda v: v not in ("None", "none", False),
        ),
    }

    @classmethod
    def can_parse(cls, content: str) -> bool:
        """Check if content looks like an Alacritty config."""
        # Alacritty uses TOML or YAML with specific section names
        alacritty_markers = [
            "[colors]",
            "[font]",
            "[cursor]",
            "[window]",
            "[shell]",
            "[terminal]",
            "[keyboard]",
            "[hints]",
            "[general]",
            "colors:",
            "font:",
            "cursor:",
            "window:",
            "shell:",
            "terminal:",
        ]
        # Also check for Alacritty-specific nested keys
        alacritty_keys = [
            "colors.primary",
            "colors.normal",
            "colors.bright",
            "font.normal",
            "window.dimensions",
        ]
        content_lower = content.lower()
        for marker in alacritty_markers:
            if marker.lower() in content_lower:
                return True
        for key in alacritty_keys:
            if key in content:
                return True
        return False

    @classmethod
    def _parse_color(cls, color_data: str | dict) -> Color | None:
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
    def _parse_hints(cls, hints_data: dict, ctec: CTEC) -> None:
        """Parse Alacritty [hints] section into CTEC TextHintConfig."""
        config = TextHintConfig()

        # Parse alphabet setting
        if "alphabet" in hints_data:
            config.alphabet = hints_data["alphabet"]

        # Parse enabled hints array
        if "enabled" in hints_data:
            for hint_entry in hints_data["enabled"]:
                rule = TextHintRule()

                # Parse pattern matching
                if "regex" in hint_entry:
                    rule.regex = hint_entry["regex"]
                if "hyperlinks" in hint_entry:
                    rule.hyperlinks = hint_entry["hyperlinks"]

                # Parse action
                if "action" in hint_entry:
                    action_str = hint_entry["action"]
                    if action_str in cls.HINT_ACTION_MAP:
                        rule.action = cls.HINT_ACTION_MAP[action_str]
                    else:
                        ctec.add_warning(f"Unknown hint action: {action_str}")

                # Parse command
                if "command" in hint_entry:
                    cmd = hint_entry["command"]
                    if isinstance(cmd, str):
                        rule.command = cmd
                    elif isinstance(cmd, dict):
                        rule.command = cmd.get("program")
                        if "args" in cmd:
                            rule.command_args = cmd["args"]

                # Parse post-processing and persist
                if "post_processing" in hint_entry:
                    rule.post_processing = hint_entry["post_processing"]
                if "persist" in hint_entry:
                    rule.persist = hint_entry["persist"]

                # Parse keyboard binding
                if "binding" in hint_entry:
                    binding_data = hint_entry["binding"]
                    rule.binding = TextHintBinding(
                        key=binding_data.get("key"),
                        mods=binding_data.get("mods", "").split("+")
                        if binding_data.get("mods")
                        else [],
                        mode=binding_data.get("mode"),
                    )

                # Parse mouse binding
                if "mouse" in hint_entry:
                    mouse_data = hint_entry["mouse"]
                    rule.mouse = TextHintMouseBinding(
                        mods=mouse_data.get("mods", "").split("+")
                        if mouse_data.get("mods")
                        else [],
                        enabled=mouse_data.get("enabled"),
                    )

                config.rules.append(rule)

        # Only set if we have any content
        if config.alphabet or config.rules:
            config.enabled = True
            ctec.text_hints = config

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
            # Try to detect format from content
            # Check source path suffix if available
            source_path = Path(source) if source else None
            if source_path and source_path.suffix == ".toml":
                is_toml = True
            else:
                # Content-based detection: look for TOML patterns
                # Skip comment lines and blank lines at the start
                is_toml = False
                for line in content.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    # First non-comment line - check for TOML patterns
                    is_toml = stripped.startswith("[") or "=" in stripped
                    break

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
                    cursor.style = cls.get_cursor_style(style_data)
                elif isinstance(style_data, dict) and "shape" in style_data:
                    cursor.style = cls.get_cursor_style(style_data["shape"])
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
        window = WindowConfig()

        def on_error(k: str, v, e: Exception) -> None:
            ctec.add_warning(f"Invalid window config {k}: {v}")

        # Handle blur separately as it has custom logic
        if "window" in data and "blur" in data["window"]:
            blur_val = data["window"]["blur"]
            if isinstance(blur_val, bool):
                window.blur = 20 if blur_val else None
            elif isinstance(blur_val, int):
                window.blur = blur_val if blur_val > 0 else None

        # Apply standard mappings
        if cls.apply_key_mapping(data, window, cls.WINDOW_MAPPING, on_error):
            ctec.window = window
        elif window.blur is not None:
            # If only blur was set
            ctec.window = window

        # Parse shell/behavior - check modern [terminal.shell] first, then legacy [shell]
        shell_data = None
        if "terminal" in data and isinstance(data["terminal"], dict):
            if "shell" in data["terminal"]:
                shell_data = data["terminal"]["shell"]
        if shell_data is None and "shell" in data:
            # Legacy fallback
            shell_data = data["shell"]

        if shell_data is not None:
            behavior = BehaviorConfig()
            if isinstance(shell_data, str):
                behavior.shell = shell_data
            elif isinstance(shell_data, dict):
                if "program" in shell_data:
                    behavior.shell = shell_data["program"]
                if "args" in shell_data:
                    behavior.shell_args = shell_data["args"]
            ctec.behavior = behavior

        # Parse environment variables
        if "env" in data:
            if ctec.behavior is None:
                ctec.behavior = BehaviorConfig()
            env_data = data["env"]
            if isinstance(env_data, dict):
                ctec.behavior.environment_variables = {
                    str(k): str(v) for k, v in env_data.items()
                }

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
                if "key" in binding:
                    mods = (
                        binding.get("mods", "").split("+")
                        if binding.get("mods")
                        else []
                    )
                    if "action" in binding:
                        kb = KeyBinding(
                            action=binding["action"],
                            key=binding["key"],
                            mods=mods,
                            mode=binding.get("mode"),
                        )
                        ctec.key_bindings.append(kb)
                    elif "chars" in binding:
                        # Keybindings using chars send raw characters instead of actions
                        # Store as terminal-specific for round-trip preservation
                        chars_value = binding["chars"]
                        mode_str = (
                            f",mode={binding['mode']}" if binding.get("mode") else ""
                        )
                        mods_str = (
                            f",mods={binding['mods']}" if binding.get("mods") else ""
                        )
                        ctec.add_terminal_specific(
                            "alacritty",
                            f"keyboard.binding.chars:{binding['key']}{mods_str}{mode_str}",
                            chars_value,
                        )
                        ctec.add_warning(
                            f"Keybinding '{binding['key']}' uses 'chars' field to send raw characters. "
                            "This is Alacritty-specific and cannot be converted to other terminals."
                        )
                    elif "command" in binding:
                        # Keybindings using command execute external programs
                        # Store as terminal-specific for round-trip preservation
                        cmd_value = binding["command"]
                        mode_str = (
                            f",mode={binding['mode']}" if binding.get("mode") else ""
                        )
                        mods_str = (
                            f",mods={binding['mods']}" if binding.get("mods") else ""
                        )
                        ctec.add_terminal_specific(
                            "alacritty",
                            f"keyboard.binding.command:{binding['key']}{mods_str}{mode_str}",
                            cmd_value,
                        )
                        ctec.add_warning(
                            f"Keybinding '{binding['key']}' uses 'command' field to execute a program. "
                            "This is Alacritty-specific and cannot be converted to other terminals."
                        )
        # Legacy format
        elif "key_bindings" in data:
            for binding in data["key_bindings"]:
                if "key" in binding:
                    mods = (
                        binding.get("mods", "").split("|")
                        if binding.get("mods")
                        else []
                    )
                    if "action" in binding:
                        kb = KeyBinding(
                            action=binding["action"],
                            key=binding["key"],
                            mods=mods,
                            mode=binding.get("mode"),
                        )
                        ctec.key_bindings.append(kb)
                    elif "chars" in binding:
                        chars_value = binding["chars"]
                        mode_str = (
                            f",mode={binding['mode']}" if binding.get("mode") else ""
                        )
                        mods_str = (
                            f",mods={binding['mods']}" if binding.get("mods") else ""
                        )
                        ctec.add_terminal_specific(
                            "alacritty",
                            f"key_bindings.chars:{binding['key']}{mods_str}{mode_str}",
                            chars_value,
                        )
                        ctec.add_warning(
                            f"Keybinding '{binding['key']}' uses 'chars' field to send raw characters. "
                            "This is Alacritty-specific and cannot be converted to other terminals."
                        )

        # Parse hints section (regex-based pattern detection)
        if "hints" in data:
            cls._parse_hints(data["hints"], ctec)

        # Store unrecognized top-level keys
        recognized_keys = {
            "colors",
            "font",
            "cursor",
            "window",
            "shell",
            "env",
            "terminal",
            "scrolling",
            "bell",
            "mouse",
            "selection",
            "keyboard",
            "key_bindings",
            "hints",
            "general",
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
                style["shape"] = str(
                    cls.get_cursor_style_value(ctec.cursor.style)
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

        # Export behavior - use modern [terminal.shell] for TOML format
        if ctec.behavior:
            if ctec.behavior.shell or ctec.behavior.shell_args:
                shell_config: dict = {}
                if ctec.behavior.shell:
                    shell_config["program"] = ctec.behavior.shell
                if ctec.behavior.shell_args:
                    shell_config["args"] = ctec.behavior.shell_args
                if shell_config:
                    if use_toml:
                        # Modern Alacritty (0.13+) uses [terminal.shell]
                        if "terminal" not in result:
                            result["terminal"] = {}
                        result["terminal"]["shell"] = shell_config
                    else:
                        # Legacy YAML format uses [shell]
                        result["shell"] = shell_config
            if ctec.behavior.environment_variables:
                result["env"] = ctec.behavior.environment_variables
            if ctec.behavior.bell_mode is not None:
                if ctec.behavior.bell_mode == BellMode.NONE:
                    result["bell"] = {"duration": 0}
                else:
                    result["bell"] = {"duration": 100}
            if ctec.behavior.copy_on_select is not None:
                result["selection"] = {
                    "save_to_clipboard": ctec.behavior.copy_on_select
                }

        # Warn about unsupported tabs and panes
        if ctec.tabs:
            ctec.add_warning(
                "Alacritty does not support native tabs. Tab configuration will not be exported. "
                "Consider using a terminal multiplexer like tmux or zellij for tab functionality."
            )
        if ctec.panes:
            ctec.add_warning(
                "Alacritty does not support native split panes. Pane configuration will not be exported. "
                "Consider using a terminal multiplexer like tmux or zellij for pane functionality."
            )

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
        # Keybinding actions that involve tabs/panes (not supported in Alacritty)
        tab_pane_actions = {
            "new_tab",
            "newtab",
            "close_tab",
            "closetab",
            "next_tab",
            "nexttab",
            "previous_tab",
            "previoustab",
            "tab:",  # prefix for tab actions
            "goto_tab",
            "gototab",
            "move_tab",
            "movetab",
            "new_split",
            "newsplit",
            "split_horizontal",
            "splithorizontal",
            "split_vertical",
            "splitvertical",
            "close_pane",
            "closepane",
            "focus_pane",
            "focuspane",
            "resize_pane",
            "resizepane",
            "toggle_split_zoom",
        }

        if ctec.key_bindings:
            bindings = []
            skipped_count = 0
            tab_pane_kb_warned = False
            for kb in ctec.key_bindings:
                # Check if keybinding is for tab/pane functionality
                action_lower = (kb.action or "").lower()
                if any(action_lower.startswith(ta) for ta in tab_pane_actions):
                    if not tab_pane_kb_warned:
                        ctec.add_warning(
                            "Keybindings for tab/pane operations cannot be exported to Alacritty "
                            "as it does not support native tabs or panes."
                        )
                        tab_pane_kb_warned = True
                    skipped_count += 1
                    continue
                # Check for unsupported features
                if kb.key_sequence:
                    ctec.add_warning(
                        f"Keybinding with key sequence '{'>'.join(kb.key_sequence)}' cannot be "
                        "exported to Alacritty. Key sequences (leader keys) are not supported."
                    )
                    skipped_count += 1
                    continue
                if kb.scope and kb.scope != KeyBindingScope.APPLICATION:
                    ctec.add_warning(
                        f"Keybinding '{kb.key}' has scope '{kb.scope.value}' which is not supported "
                        "in Alacritty. It will be exported as a regular (application-scoped) binding."
                    )
                # Build full action with parameter if present
                action = (
                    kb.get_full_action()
                    if hasattr(kb, "get_full_action")
                    else kb.action
                )
                binding = {"key": kb.key, "action": action}
                if kb.mods:
                    binding["mods"] = "+".join(kb.mods)
                if kb.mode:
                    binding["mode"] = kb.mode
                bindings.append(binding)
            if bindings:
                result["keyboard"] = {"bindings": bindings}

        # Export hints (text pattern detection)
        if ctec.text_hints and ctec.text_hints.rules:
            hints: dict = {}
            if ctec.text_hints.alphabet:
                hints["alphabet"] = ctec.text_hints.alphabet

            enabled_hints = []
            for rule in ctec.text_hints.rules:
                hint_entry: dict = {}

                # Export pattern matching
                if rule.regex:
                    hint_entry["regex"] = rule.regex
                if rule.hyperlinks is not None:
                    hint_entry["hyperlinks"] = rule.hyperlinks

                # Export action
                if rule.action:
                    alac_action = cls.HINT_ACTION_REVERSE_MAP.get(rule.action)
                    if alac_action:
                        hint_entry["action"] = alac_action
                    elif rule.action == TextHintAction.OPEN:
                        # Default open command varies by platform
                        pass  # Let command handle it

                # Export command
                if rule.command:
                    if rule.command_args:
                        hint_entry["command"] = {
                            "program": rule.command,
                            "args": rule.command_args,
                        }
                    else:
                        hint_entry["command"] = rule.command

                # Export post-processing and persist
                if rule.post_processing is not None:
                    hint_entry["post_processing"] = rule.post_processing
                if rule.persist is not None:
                    hint_entry["persist"] = rule.persist

                # Export keyboard binding
                if rule.binding:
                    binding_dict: dict = {}
                    if rule.binding.key:
                        binding_dict["key"] = rule.binding.key
                    if rule.binding.mods:
                        binding_dict["mods"] = "+".join(rule.binding.mods)
                    if rule.binding.mode:
                        binding_dict["mode"] = rule.binding.mode
                    if binding_dict:
                        hint_entry["binding"] = binding_dict

                # Export mouse binding
                if rule.mouse:
                    mouse_dict: dict = {}
                    if rule.mouse.mods:
                        mouse_dict["mods"] = "+".join(rule.mouse.mods)
                    if rule.mouse.enabled is not None:
                        mouse_dict["enabled"] = rule.mouse.enabled
                    if mouse_dict:
                        hint_entry["mouse"] = mouse_dict

                if hint_entry:
                    enabled_hints.append(hint_entry)

            if enabled_hints:
                hints["enabled"] = enabled_hints

            if hints:
                result["hints"] = hints

        # Restore terminal-specific settings
        for setting in ctec.get_terminal_specific("alacritty"):
            result[setting.key] = setting.value

        if use_toml:
            return tomli_w.dumps(result)
        else:
            return yaml.dump(result, default_flow_style=False, sort_keys=False)
