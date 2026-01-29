"""
iTerm2 configuration adapter.

iTerm2 uses a macOS plist format for its configuration, stored in
~/Library/Preferences/com.googlecode.iterm2.plist

Color schemes can also be stored as separate .itermcolors files.
"""

import plistlib
from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    QuickTerminalConfig,
    QuickTerminalPosition,
    ScrollConfig,
    TextHintAction,
    TextHintConfig,
    TextHintPrecision,
    TextHintRule,
    WindowConfig,
)
from console_cowboy.utils.colors import color_to_float_tuple, float_tuple_to_color
from console_cowboy.utils.fonts import (
    friendly_to_postscript,
    is_postscript_name,
    postscript_to_friendly,
)

from .base import TerminalAdapter


class ITerm2Adapter(TerminalAdapter):
    """
    Adapter for iTerm2 terminal emulator.

    Supports parsing:
    - Full iTerm2 plist configuration
    - .itermcolors color scheme files

    Note: iTerm2 uses plist format with colors stored as floating point
    RGB values (0.0-1.0).
    """

    name = "iterm2"
    display_name = "iTerm2"
    description = "macOS terminal emulator with extensive customization options"
    config_extensions = [".plist", ".itermcolors"]
    default_config_paths = [
        "Library/Preferences/com.googlecode.iterm2.plist",
    ]

    # Mapping of iTerm2 cursor styles to CTEC
    CURSOR_STYLE_MAP = {
        0: CursorStyle.UNDERLINE,
        1: CursorStyle.BLOCK,
        2: CursorStyle.BEAM,
    }

    CURSOR_STYLE_REVERSE_MAP = {v: k for k, v in CURSOR_STYLE_MAP.items()}

    # Color key mappings from iTerm2 to CTEC
    # Aligned with iTerm2-Color-Schemes extended YAML format
    COLOR_KEY_MAP = {
        # Core semantic colors
        "Foreground Color": "foreground",
        "Background Color": "background",
        "Cursor Color": "cursor",
        "Cursor Text Color": "cursor_text",
        "Selection Color": "selection",
        "Selected Text Color": "selection_text",
        # Extended semantic colors (iTerm2-Color-Schemes YAML extensions)
        "Bold Color": "bold",
        "Link Color": "link",
        "Underline Color": "underline",
        "Cursor Guide Color": "cursor_guide",
        # ANSI colors (0-15)
        "Ansi 0 Color": "black",
        "Ansi 1 Color": "red",
        "Ansi 2 Color": "green",
        "Ansi 3 Color": "yellow",
        "Ansi 4 Color": "blue",
        "Ansi 5 Color": "magenta",
        "Ansi 6 Color": "cyan",
        "Ansi 7 Color": "white",
        "Ansi 8 Color": "bright_black",
        "Ansi 9 Color": "bright_red",
        "Ansi 10 Color": "bright_green",
        "Ansi 11 Color": "bright_yellow",
        "Ansi 12 Color": "bright_blue",
        "Ansi 13 Color": "bright_magenta",
        "Ansi 14 Color": "bright_cyan",
        "Ansi 15 Color": "bright_white",
    }

    COLOR_KEY_REVERSE_MAP = {v: k for k, v in COLOR_KEY_MAP.items()}

    # Mapping of iTerm2 Hotkey Window Type to QuickTerminalPosition
    # This is a separate property from Window Type, specific to hotkey windows
    # iTerm2 values: 0=floating, 1=fullscreen, 2=left, 3=right, 4=bottom, 5=top
    HOTKEY_WINDOW_TYPE_MAP = {
        0: QuickTerminalPosition.FLOATING,
        1: QuickTerminalPosition.FULLSCREEN,
        2: QuickTerminalPosition.LEFT,
        3: QuickTerminalPosition.RIGHT,
        4: QuickTerminalPosition.BOTTOM,
        5: QuickTerminalPosition.TOP,
    }

    HOTKEY_WINDOW_TYPE_REVERSE_MAP = {v: k for k, v in HOTKEY_WINDOW_TYPE_MAP.items()}

    # Mapping of iTerm2 Window Type enum to quick terminal positions
    # Window Type is a general profile property that can indicate edge positioning
    # Values 4-11 indicate edge-anchored windows suitable for quick terminal
    WINDOW_TYPE_TO_QUICK_POSITION = {
        4: QuickTerminalPosition.BOTTOM,  # Full-Width Bottom of Screen
        5: QuickTerminalPosition.TOP,  # Full-Width Top of Screen
        6: QuickTerminalPosition.LEFT,  # Full Height Left of Screen
        7: QuickTerminalPosition.RIGHT,  # Full Height Right of Screen
        8: QuickTerminalPosition.BOTTOM,  # Bottom of Screen
        9: QuickTerminalPosition.TOP,  # Top of Screen
        10: QuickTerminalPosition.LEFT,  # Left of Screen
        11: QuickTerminalPosition.RIGHT,  # Right of Screen
    }

    # Window Type values that indicate full-width/full-height edge windows
    WINDOW_TYPE_FULL_EDGE = {4, 5, 6, 7}  # Full-width or full-height

    # Window Type enum values for reference:
    # 0: Normal
    # 1: Full Screen
    # 2: Maximized
    # 3: No Title Bar
    # 4: Full-Width Bottom of Screen
    # 5: Full-Width Top of Screen
    # 6: Full Height Left of Screen
    # 7: Full Height Right of Screen
    # 8: Bottom of Screen
    # 9: Top of Screen
    # 10: Left of Screen
    # 11: Right of Screen

    # iTerm2 Smart Selection action mapping to CTEC
    # iTerm2 action titles from Preferences > Profiles > Advanced > Smart Selection
    SMART_SELECTION_ACTION_MAP = {
        "Open File": TextHintAction.OPEN_FILE,
        "Open URL": TextHintAction.OPEN_URL,
        "Run Command...": TextHintAction.RUN_COMMAND,
        "Run Coprocess...": TextHintAction.RUN_COPROCESS,
        "Send Text...": TextHintAction.SEND_TEXT,
        "Run Command in Window...": TextHintAction.RUN_COMMAND_IN_WINDOW,
        "Copy": TextHintAction.COPY,
    }

    SMART_SELECTION_ACTION_REVERSE_MAP = {
        v: k for k, v in SMART_SELECTION_ACTION_MAP.items()
    }

    # iTerm2 Smart Selection precision mapping
    SMART_SELECTION_PRECISION_MAP = {
        0: TextHintPrecision.VERY_LOW,
        1: TextHintPrecision.LOW,
        2: TextHintPrecision.NORMAL,
        3: TextHintPrecision.HIGH,
        4: TextHintPrecision.VERY_HIGH,
    }

    SMART_SELECTION_PRECISION_REVERSE_MAP = {
        v: k for k, v in SMART_SELECTION_PRECISION_MAP.items()
    }

    @classmethod
    def _parse_iterm_color(cls, color_dict: dict) -> Color:
        """Parse an iTerm2 color dictionary to a Color object."""
        # iTerm2 uses "Color Space" and RGB component keys
        r = color_dict.get("Red Component", 0.0)
        g = color_dict.get("Green Component", 0.0)
        b = color_dict.get("Blue Component", 0.0)
        return float_tuple_to_color((r, g, b))

    @classmethod
    def _export_color(cls, color: Color) -> dict:
        """Export a Color to iTerm2 color dictionary format."""
        r, g, b = color_to_float_tuple(color)
        return {
            "Color Space": "sRGB",
            "Red Component": r,
            "Green Component": g,
            "Blue Component": b,
        }

    @classmethod
    def _parse_color_scheme(cls, profile: dict) -> ColorScheme:
        """Parse color settings from an iTerm2 profile."""
        scheme = ColorScheme()
        for iterm_key, ctec_key in cls.COLOR_KEY_MAP.items():
            if iterm_key in profile:
                color = cls._parse_iterm_color(profile[iterm_key])
                setattr(scheme, ctec_key, color)
        return scheme

    @classmethod
    def _parse_smart_selection_rules(cls, rules_data: list, ctec: CTEC) -> None:
        """Parse iTerm2 Smart Selection Rules into CTEC TextHintConfig.

        iTerm2 Smart Selection Rules are a list of dictionaries with:
        - regex: The pattern to match (ICU regex syntax)
        - precision: Match priority (0=very_low to 4=very_high)
        - notes: Description of the rule
        - actions: List of action dictionaries with 'title' and 'action' (parameter)
        """
        if not rules_data:
            return

        config = TextHintConfig(enabled=True)

        for rule_data in rules_data:
            rule = TextHintRule()

            # Parse regex pattern
            if "regex" in rule_data:
                rule.regex = rule_data["regex"]

            # Parse precision level
            if "precision" in rule_data:
                precision_val = rule_data["precision"]
                if precision_val in cls.SMART_SELECTION_PRECISION_MAP:
                    rule.precision = cls.SMART_SELECTION_PRECISION_MAP[precision_val]

            # Parse notes (description)
            if "notes" in rule_data:
                rule.notes = rule_data["notes"]

            # Parse actions - iTerm2 can have multiple actions per rule
            # We'll use the first action as the primary action
            if "actions" in rule_data and rule_data["actions"]:
                actions = rule_data["actions"]
                if actions:
                    first_action = actions[0]
                    action_title = first_action.get("title", "")
                    if action_title in cls.SMART_SELECTION_ACTION_MAP:
                        rule.action = cls.SMART_SELECTION_ACTION_MAP[action_title]
                    # Store the action parameter (command/text to send)
                    if "action" in first_action:
                        rule.parameter = first_action["action"]

            # Only add if we have at least a regex
            if rule.regex:
                config.rules.append(rule)

        if config.rules:
            ctec.text_hints = config

    @classmethod
    def _parse_profile_into_ctec(cls, profile_data: dict, ctec: CTEC) -> None:
        """Parse an iTerm2 profile's settings directly into a CTEC object."""
        # Parse color scheme
        ctec.color_scheme = cls._parse_color_scheme(profile_data)

        # Parse font configuration
        if "Normal Font" in profile_data:
            font_str = profile_data["Normal Font"]
            # iTerm2 font format: "FontName Size"
            parts = font_str.rsplit(" ", 1)
            if len(parts) == 2:
                font_family = parts[0]
                font_size = (
                    float(parts[1]) if parts[1].replace(".", "").isdigit() else None
                )
            else:
                font_family = font_str
                font_size = None

            # Convert PostScript name to friendly and store original
            if is_postscript_name(font_family):
                friendly_family = postscript_to_friendly(font_family)
                ctec.font = FontConfig(family=friendly_family, size=font_size)
                ctec.font.set_source_name("iterm2", font_family)
            else:
                ctec.font = FontConfig(family=font_family, size=font_size)

        # Handle Non-ASCII Font as fallback font
        if "Non-ASCII Font" in profile_data and profile_data.get(
            "Use Non-ASCII Font", False
        ):
            non_ascii_str = profile_data["Non-ASCII Font"]
            non_ascii_parts = non_ascii_str.rsplit(" ", 1)
            non_ascii_family = non_ascii_parts[0] if non_ascii_parts else non_ascii_str
            # Convert to friendly name
            if is_postscript_name(non_ascii_family):
                non_ascii_family = postscript_to_friendly(non_ascii_family)
            if ctec.font:
                ctec.font.fallback_fonts = [non_ascii_family]
                # Store original for lossless round-trip (includes size)
                ctec.font.set_source_name("iterm2_non_ascii", non_ascii_str)
            else:
                ctec.font = FontConfig(fallback_fonts=[non_ascii_family])
                ctec.font.set_source_name("iterm2_non_ascii", non_ascii_str)

        # Handle anti-aliasing
        if "ASCII Anti Aliased" in profile_data:
            if ctec.font:
                ctec.font.anti_aliasing = profile_data["ASCII Anti Aliased"]
            else:
                ctec.font = FontConfig(anti_aliasing=profile_data["ASCII Anti Aliased"])

        # Handle Powerline glyphs
        if "Draw Powerline Glyphs" in profile_data:
            if ctec.font:
                ctec.font.draw_powerline_glyphs = profile_data["Draw Powerline Glyphs"]
            else:
                ctec.font = FontConfig(
                    draw_powerline_glyphs=profile_data["Draw Powerline Glyphs"]
                )

        # Parse cursor configuration
        cursor_config = CursorConfig()
        if "Cursor Type" in profile_data:
            cursor_type = profile_data["Cursor Type"]
            cursor_config.style = cls.CURSOR_STYLE_MAP.get(
                cursor_type, CursorStyle.BLOCK
            )
        if "Blinking Cursor" in profile_data:
            cursor_config.blink = profile_data["Blinking Cursor"]
        ctec.cursor = cursor_config

        # Parse behavior configuration
        behavior = BehaviorConfig()
        if "Command" in profile_data:
            behavior.shell = profile_data["Command"]
        if "Working Directory" in profile_data:
            behavior.working_directory = profile_data["Working Directory"]
        if "Silence Bell" in profile_data:
            if profile_data["Silence Bell"]:
                behavior.bell_mode = BellMode.NONE
            elif profile_data.get("Visual Bell", False):
                behavior.bell_mode = BellMode.VISUAL
            else:
                behavior.bell_mode = BellMode.AUDIBLE
        ctec.behavior = behavior

        # Parse scroll settings
        if profile_data.get("Unlimited Scrollback", False):
            ctec.scroll = ScrollConfig(unlimited=True)
        elif "Scrollback Lines" in profile_data:
            lines = profile_data["Scrollback Lines"]
            if lines == 0:
                ctec.scroll = ScrollConfig(disabled=True)
            else:
                ctec.scroll = ScrollConfig(lines=lines)

        # Parse window settings from profile (transparency, blur, columns, rows)
        window = ctec.window or WindowConfig()
        window_modified = False

        # Columns and Rows
        if "Columns" in profile_data:
            window.columns = profile_data["Columns"]
            window_modified = True
        if "Rows" in profile_data:
            window.rows = profile_data["Rows"]
            window_modified = True

        # Transparency: iTerm2 uses 0=opaque, 1=fully transparent
        # CTEC uses opacity where 1.0=opaque, 0.0=fully transparent
        if "Transparency" in profile_data:
            transparency = profile_data["Transparency"]
            window.opacity = 1.0 - transparency  # Invert for CTEC
            window_modified = True

        # Blur settings
        if profile_data.get("Blur", False):
            blur_radius = profile_data.get("Blur Radius", 10)
            window.blur = blur_radius
            window_modified = True

        # Parse Window Type for startup mode and decorations
        if "Window Type" in profile_data:
            window_type = profile_data["Window Type"]
            if window_type == 1:
                # Full Screen
                window.startup_mode = "fullscreen"
                window_modified = True
            elif window_type == 2:
                # Maximized
                window.startup_mode = "maximized"
                window_modified = True
            elif window_type == 3:
                # No Title Bar
                window.decorations = False
                window_modified = True

        if window_modified:
            ctec.window = window

        # Parse hotkey window (quick terminal) settings
        if profile_data.get("Has Hotkey", False):
            quick = QuickTerminalConfig(enabled=True)

            # Parse window position/type
            if "Hotkey Window Type" in profile_data:
                window_type = profile_data["Hotkey Window Type"]
                quick.position = cls.HOTKEY_WINDOW_TYPE_MAP.get(
                    window_type, QuickTerminalPosition.TOP
                )

            # Parse animation setting
            if "Hotkey Window Animates" in profile_data:
                # iTerm2 just has a boolean; we'll use a default duration
                if profile_data["Hotkey Window Animates"]:
                    quick.animation_duration = 200  # Default 200ms
                else:
                    quick.animation_duration = 0

            # Parse floating setting
            if "Hotkey Window Float" in profile_data:
                quick.floating = profile_data["Hotkey Window Float"]

            # Parse hotkey configuration
            if "Hotkey Key Code" in profile_data:
                quick.hotkey_key_code = profile_data["Hotkey Key Code"]
            if "Hotkey Modifier Flags" in profile_data:
                quick.hotkey_modifiers = profile_data["Hotkey Modifier Flags"]
            if "Hotkey Characters" in profile_data:
                # Store the character representation as the hotkey string
                quick.hotkey = profile_data["Hotkey Characters"]

            ctec.quick_terminal = quick

        # Parse Smart Selection Rules into CTEC text_hints
        if "Smart Selection Rules" in profile_data:
            cls._parse_smart_selection_rules(
                profile_data["Smart Selection Rules"], ctec
            )

        # Store iTerm2-specific settings for round-trip preservation
        # These are settings that either:
        # 1. Have no CTEC equivalent, or
        # 2. Need to be preserved exactly for iTerm2-to-iTerm2 round-trips
        specific_keys = [
            # Basic settings
            "Unlimited Scrollback",
            "Use Bold Font",
            "Use Italic Font",
            "ASCII Anti Aliased",
            "Non-ASCII Anti Aliased",
            "Ambiguous Double Width",
            "Horizontal Spacing",
            "Vertical Spacing",
            "Use Non-ASCII Font",
            "Minimum Contrast",
            # Advanced features (iTerm2-only, no equivalent in other terminals)
            "Triggers",
            # Note: Smart Selection Rules are now parsed into CTEC text_hints
            "Semantic History",
            "Bound Hosts",  # Automatic Profile Switching rules
            # Badge settings
            "Badge Text",
            "Badge Color",
            "Badge Font",
            "Badge Max Width",
            "Badge Max Height",
            "Badge Right Margin",
            "Badge Top Margin",
            # Hotkey window settings (only preserve ones not mapped to QuickTerminalConfig)
            "Hotkey Window Dock Click Action",
            # Background image settings
            "Background Image Location",
            "Background Image Mode",
            "Blend",
            # Session settings
            "Custom Directory",
            "Jobs to Ignore",
            "Keyboard Map",
            "Title Components",
            "Custom Window Title",
        ]
        for key in specific_keys:
            if key in profile_data:
                ctec.add_terminal_specific("iterm2", key, profile_data[key])

    @classmethod
    def _parse_hotkey_settings(cls, profile_data: dict, ctec: CTEC) -> None:
        """
        Extract only hotkey/quick-terminal settings from an iTerm2 profile.

        This is used to import hotkey settings from a dedicated Hotkey Window
        profile, which is how iTerm2 implements quick-terminal functionality.
        Unlike other terminals where quick-terminal is a top-level setting,
        iTerm2 uses a separate profile for the hotkey window.
        """
        if not profile_data.get("Has Hotkey", False):
            return

        quick = QuickTerminalConfig(enabled=True)

        # Parse window position from Window Type
        # Window Type values 4-11 indicate edge-positioned windows
        if "Window Type" in profile_data:
            window_type = profile_data["Window Type"]
            if window_type in cls.WINDOW_TYPE_TO_QUICK_POSITION:
                quick.position = cls.WINDOW_TYPE_TO_QUICK_POSITION[window_type]
                # Track if this is a full-width/full-height edge window
                if window_type in cls.WINDOW_TYPE_FULL_EDGE:
                    # Full edge windows span the entire edge
                    pass  # Could set a size property here if CTEC supports it
            elif window_type == 1:
                # Full Screen
                quick.position = QuickTerminalPosition.FULLSCREEN
            else:
                # Default to TOP for other window types
                quick.position = QuickTerminalPosition.TOP
        elif "Hotkey Window Type" in profile_data:
            # Fallback to Hotkey Window Type if present (separate property)
            window_type = profile_data["Hotkey Window Type"]
            quick.position = cls.HOTKEY_WINDOW_TYPE_MAP.get(
                window_type, QuickTerminalPosition.TOP
            )

        # Parse animation setting
        if "HotKey Window Animates" in profile_data:
            if profile_data["HotKey Window Animates"]:
                quick.animation_duration = 200  # Default 200ms
            else:
                quick.animation_duration = 0
        # Also check for variant spelling
        elif "Hotkey Window Animates" in profile_data:
            if profile_data["Hotkey Window Animates"]:
                quick.animation_duration = 200
            else:
                quick.animation_duration = 0

        # Parse floating setting
        if "HotKey Window Floats" in profile_data:
            quick.floating = profile_data["HotKey Window Floats"]
        elif "Hotkey Window Float" in profile_data:
            quick.floating = profile_data["Hotkey Window Float"]

        # Parse auto-hide setting (maps to hide_on_focus_loss)
        if "HotKey Window AutoHides" in profile_data:
            quick.hide_on_focus_loss = profile_data["HotKey Window AutoHides"]

        # Parse hotkey configuration
        if "HotKey Key Code" in profile_data:
            quick.hotkey_key_code = profile_data["HotKey Key Code"]
        elif "Hotkey Key Code" in profile_data:
            quick.hotkey_key_code = profile_data["Hotkey Key Code"]

        if "HotKey Modifier Flags" in profile_data:
            quick.hotkey_modifiers = profile_data["HotKey Modifier Flags"]
        elif "Hotkey Modifier Flags" in profile_data:
            quick.hotkey_modifiers = profile_data["Hotkey Modifier Flags"]

        if "HotKey Characters" in profile_data:
            quick.hotkey = profile_data["HotKey Characters"]
        elif "Hotkey Characters" in profile_data:
            quick.hotkey = profile_data["Hotkey Characters"]

        ctec.quick_terminal = quick

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
        profile_name: str | None = None,
    ) -> CTEC:
        """
        Parse an iTerm2 configuration file.

        Supports both full plist configs and .itermcolors files.

        Args:
            source: Path to the configuration file
            content: Optional string content to parse instead of reading from file
            profile_name: Optional profile name to import. If not specified,
                         uses the default profile. If multiple profiles exist
                         and no profile_name is specified, a warning is emitted.

        Returns:
            CTEC configuration object
        """
        ctec = CTEC(source_terminal="iterm2")

        if content is not None:
            data = plistlib.loads(content.encode())
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            with open(path, "rb") as f:
                data = plistlib.load(f)

        # Check if this is a color scheme file (.itermcolors)
        if "Ansi 0 Color" in data or "Foreground Color" in data:
            # This is a color scheme file
            ctec.color_scheme = cls._parse_color_scheme(data)
            return ctec

        # Full iTerm2 config
        if "New Bookmarks" in data:
            profiles = data["New Bookmarks"]

            if not profiles:
                ctec.add_warning("No profiles found in iTerm2 configuration")
                return ctec

            # Build list of profile names and find default
            profile_names = [
                p.get("Name", f"Profile {i}") for i, p in enumerate(profiles)
            ]
            default_profile_data = None
            default_profile_name = None

            for profile_data in profiles:
                if profile_data.get("Default Bookmark", "No") == "Yes":
                    default_profile_data = profile_data
                    default_profile_name = profile_data.get("Name", "Default")
                    break

            # If no explicit default, use the first profile
            if default_profile_data is None:
                default_profile_data = profiles[0]
                default_profile_name = profile_names[0]

            # Determine which profile to use
            selected_profile_data = None
            selected_profile_name = None

            if profile_name:
                # User specified a profile name
                for profile_data in profiles:
                    if profile_data.get("Name") == profile_name:
                        selected_profile_data = profile_data
                        selected_profile_name = profile_name
                        break
                if selected_profile_data is None:
                    raise ValueError(
                        f"Profile '{profile_name}' not found. "
                        f"Available profiles: {', '.join(profile_names)}"
                    )
            else:
                # Use default profile
                selected_profile_data = default_profile_data
                selected_profile_name = default_profile_name

                # Warn if multiple profiles exist
                if len(profiles) > 1:
                    other_profiles = [
                        n for n in profile_names if n != selected_profile_name
                    ]
                    ctec.add_warning(
                        f"iTerm2 config contains {len(profiles)} profiles. "
                        f"Importing '{selected_profile_name}' (default). "
                        f"Use --profile to select a different profile. "
                        f"Other profiles: {', '.join(other_profiles)}"
                    )

            # Parse the selected profile into CTEC
            cls._parse_profile_into_ctec(selected_profile_data, ctec)

            # Import hotkey settings from the designated hotkey profile
            # iTerm2 implements quick-terminal as a separate "Hotkey Window" profile,
            # unlike other terminals where it's a top-level setting.
            # The top-level HotKeyBookmark setting contains the GUID of the hotkey profile.
            if ctec.quick_terminal is None and "HotKeyBookmark" in data:
                hotkey_guid = data["HotKeyBookmark"]
                for profile_data in profiles:
                    if profile_data.get("Guid") == hotkey_guid:
                        cls._parse_hotkey_settings(profile_data, ctec)
                        break

        # Parse global window configuration (fallback if not set in profile)
        # Use existing window config to preserve opacity, blur, decorations, etc.
        if (
            "Default Bookmark Window Width" in data
            or "Default Bookmark Window Height" in data
        ):
            window = ctec.window or WindowConfig()
            if "Default Bookmark Window Width" in data and window.columns is None:
                window.columns = data["Default Bookmark Window Width"]
            if "Default Bookmark Window Height" in data and window.rows is None:
                window.rows = data["Default Bookmark Window Height"]
            ctec.window = window

        # Parse global settings
        global_specific_keys = [
            "TabStyleWithAutomaticOption",
            "HideTab",
            "HideMenuBarInFullscreen",
            "SplitPaneDimmingAmount",
            "UseBorder",
            "HideScrollbar",
            "PromptOnQuit",
            "OnlyWhenMoreTabs",
        ]
        for key in global_specific_keys:
            if key in data:
                ctec.add_terminal_specific("iterm2", key, data[key])

        return ctec

    @classmethod
    def _export_ctec_to_profile(cls, ctec: CTEC, profile_name: str = "Default") -> dict:
        """Export CTEC settings to an iTerm2 profile dictionary."""
        result = {"Name": profile_name, "Guid": profile_name.lower().replace(" ", "-")}

        # Export colors
        if ctec.color_scheme:
            for ctec_key, iterm_key in cls.COLOR_KEY_REVERSE_MAP.items():
                color = getattr(ctec.color_scheme, ctec_key, None)
                if color:
                    result[iterm_key] = cls._export_color(color)

        # Export font
        if ctec.font and ctec.font.family:
            size = ctec.font.size or 12
            # Use stored PostScript name for lossless round-trip, otherwise convert
            ps_name = ctec.font.get_source_name("iterm2")
            if ps_name:
                font_name = ps_name
            else:
                # Convert friendly name to PostScript
                font_name = friendly_to_postscript(ctec.font.family)
            result["Normal Font"] = f"{font_name} {size}"

            # Export fallback fonts as Non-ASCII Font
            if ctec.font.fallback_fonts:
                # Use stored original for lossless round-trip, otherwise convert
                non_ascii_original = ctec.font.get_source_name("iterm2_non_ascii")
                if non_ascii_original:
                    result["Non-ASCII Font"] = non_ascii_original
                else:
                    fallback = ctec.font.fallback_fonts[0]
                    fallback_ps = friendly_to_postscript(fallback)
                    result["Non-ASCII Font"] = f"{fallback_ps} {size}"
                result["Use Non-ASCII Font"] = True

            # Export anti-aliasing
            if ctec.font.anti_aliasing is not None:
                result["ASCII Anti Aliased"] = ctec.font.anti_aliasing
                result["Non-ASCII Anti Aliased"] = ctec.font.anti_aliasing

            # Export Powerline glyphs
            if ctec.font.draw_powerline_glyphs is not None:
                result["Draw Powerline Glyphs"] = ctec.font.draw_powerline_glyphs

        # Export cursor
        if ctec.cursor:
            if ctec.cursor.style:
                result["Cursor Type"] = cls.CURSOR_STYLE_REVERSE_MAP.get(
                    ctec.cursor.style, 1
                )
            if ctec.cursor.blink is not None:
                result["Blinking Cursor"] = ctec.cursor.blink

        # Export behavior
        if ctec.behavior:
            if ctec.behavior.shell:
                result["Command"] = ctec.behavior.shell
                result["Custom Command"] = "Yes"
            if ctec.behavior.working_directory:
                result["Working Directory"] = ctec.behavior.working_directory
                result["Custom Directory"] = "Yes"
            if ctec.behavior.bell_mode is not None:
                result["Silence Bell"] = ctec.behavior.bell_mode == BellMode.NONE
                result["Visual Bell"] = ctec.behavior.bell_mode == BellMode.VISUAL

        # Export scroll settings from CTEC scroll config
        if ctec.scroll:
            if ctec.scroll.unlimited:
                result["Unlimited Scrollback"] = True
                result["Scrollback Lines"] = 0
            elif ctec.scroll.disabled:
                result["Unlimited Scrollback"] = False
                result["Scrollback Lines"] = 0
            elif ctec.scroll.lines is not None:
                result["Unlimited Scrollback"] = False
                result["Scrollback Lines"] = ctec.scroll.lines

        # Export window settings (transparency, blur)
        if ctec.window:
            # Opacity: CTEC uses 1.0=opaque, iTerm2 uses 0=opaque (Transparency)
            if ctec.window.opacity is not None:
                result["Transparency"] = 1.0 - ctec.window.opacity  # Invert for iTerm2

            # Blur
            if ctec.window.blur is not None and ctec.window.blur > 0:
                result["Blur"] = True
                result["Blur Radius"] = ctec.window.blur

            # Columns and Rows
            if ctec.window.columns is not None:
                result["Columns"] = ctec.window.columns
            if ctec.window.rows is not None:
                result["Rows"] = ctec.window.rows

        # Export quick terminal (hotkey window) settings
        if ctec.quick_terminal and ctec.quick_terminal.enabled:
            result["Has Hotkey"] = True

            # Export position as Hotkey Window Type
            if ctec.quick_terminal.position is not None:
                window_type = cls.HOTKEY_WINDOW_TYPE_REVERSE_MAP.get(
                    ctec.quick_terminal.position,
                    5,  # Default to TOP
                )
                result["Hotkey Window Type"] = window_type

            # Export animation
            if ctec.quick_terminal.animation_duration is not None:
                result["Hotkey Window Animates"] = (
                    ctec.quick_terminal.animation_duration > 0
                )

            # Export floating
            if ctec.quick_terminal.floating is not None:
                result["Hotkey Window Float"] = ctec.quick_terminal.floating

            # Export hotkey configuration
            if ctec.quick_terminal.hotkey_key_code is not None:
                result["Hotkey Key Code"] = ctec.quick_terminal.hotkey_key_code
            if ctec.quick_terminal.hotkey_modifiers is not None:
                result["Hotkey Modifier Flags"] = ctec.quick_terminal.hotkey_modifiers
            if ctec.quick_terminal.hotkey is not None:
                result["Hotkey Characters"] = ctec.quick_terminal.hotkey

        # Export text hints as Smart Selection Rules
        if ctec.text_hints and ctec.text_hints.rules:
            smart_selection_rules = []
            for rule in ctec.text_hints.rules:
                rule_dict: dict = {}

                # Export regex pattern
                if rule.regex:
                    rule_dict["regex"] = rule.regex

                # Export precision level (default to NORMAL if not specified)
                precision_val = cls.SMART_SELECTION_PRECISION_REVERSE_MAP.get(
                    rule.precision,
                    2,  # NORMAL
                )
                rule_dict["precision"] = precision_val

                # Export notes (description)
                if rule.notes:
                    rule_dict["notes"] = rule.notes

                # Export action
                if rule.action:
                    action_title = cls.SMART_SELECTION_ACTION_REVERSE_MAP.get(
                        rule.action
                    )
                    if action_title:
                        action_entry = {"title": action_title}
                        if rule.parameter:
                            action_entry["action"] = rule.parameter
                        elif rule.command:
                            # Use command as the action parameter
                            action_entry["action"] = rule.command
                        rule_dict["actions"] = [action_entry]

                if rule_dict.get("regex"):
                    smart_selection_rules.append(rule_dict)

            if smart_selection_rules:
                result["Smart Selection Rules"] = smart_selection_rules

        # Restore terminal-specific settings (no longer profile-prefixed)
        for setting in ctec.get_terminal_specific("iterm2"):
            # Skip global settings, only include profile-level ones
            global_keys = [
                "TabStyleWithAutomaticOption",
                "HideTab",
                "HideMenuBarInFullscreen",
                "SplitPaneDimmingAmount",
                "UseBorder",
                "HideScrollbar",
                "PromptOnQuit",
                "OnlyWhenMoreTabs",
            ]
            if setting.key not in global_keys:
                result[setting.key] = setting.value

        return result

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """
        Export CTEC to iTerm2 plist format.

        Creates a single profile named "Default" from the CTEC settings.

        Returns a plist XML string that can be saved to a file.
        """
        result = {}

        # Create a single profile from CTEC settings
        profile = cls._export_ctec_to_profile(ctec)
        result["New Bookmarks"] = [profile]

        # Export window configuration
        if ctec.window:
            if ctec.window.columns:
                result["Default Bookmark Window Width"] = ctec.window.columns
            if ctec.window.rows:
                result["Default Bookmark Window Height"] = ctec.window.rows

        # Restore terminal-specific global settings
        global_keys = [
            "TabStyleWithAutomaticOption",
            "HideTab",
            "HideMenuBarInFullscreen",
            "SplitPaneDimmingAmount",
            "UseBorder",
            "HideScrollbar",
            "PromptOnQuit",
            "OnlyWhenMoreTabs",
        ]
        for setting in ctec.get_terminal_specific("iterm2"):
            if setting.key in global_keys:
                result[setting.key] = setting.value

        return plistlib.dumps(result).decode()

    @classmethod
    def export_color_scheme(cls, color_scheme: ColorScheme) -> str:
        """
        Export a ColorScheme to .itermcolors format.

        Args:
            color_scheme: Color scheme to export

        Returns:
            Plist XML string for .itermcolors file
        """
        result = {}
        for ctec_key, iterm_key in cls.COLOR_KEY_REVERSE_MAP.items():
            color = getattr(color_scheme, ctec_key, None)
            if color:
                result[iterm_key] = cls._export_color(color)
        return plistlib.dumps(result).decode()
