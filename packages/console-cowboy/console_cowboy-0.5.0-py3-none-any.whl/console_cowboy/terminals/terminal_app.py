"""
macOS Terminal.app configuration adapter.

Terminal.app uses a macOS plist format for its configuration, stored in
~/Library/Preferences/com.apple.Terminal.plist

Individual profiles can also be exported as .terminal files.

Colors and fonts are stored as NSKeyedArchiver-encoded NSData blobs,
which requires special handling (see utils/nsarchive.py). Font names
should be in PostScript format for proper NSFont resolution.
"""

import plistlib
from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.utils.fonts import (
    friendly_to_postscript,
    is_postscript_name,
    postscript_to_friendly,
)
from console_cowboy.utils.nsarchive import (
    decode_nscolor_data,
    decode_nsfont_data,
    encode_nscolor_data,
    encode_nsfont_data,
)

from .base import TerminalAdapter


class TerminalAppAdapter(TerminalAdapter):
    """
    Adapter for macOS Terminal.app.

    Supports parsing:
    - Full com.apple.Terminal.plist configuration (multiple profiles)
    - Exported .terminal profile files (single profile)

    Note: Terminal.app uses NSKeyedArchiver encoding for colors and fonts,
    which works best on macOS with PyObjC. Without PyObjC, a manual parser
    is used which may have limited compatibility.
    """

    name = "terminal_app"
    display_name = "Terminal.app"
    description = "macOS built-in terminal emulator"
    config_extensions = [".terminal", ".plist"]
    default_config_paths = [
        "Library/Preferences/com.apple.Terminal.plist",
    ]

    # Cursor type mapping (Terminal.app uses different values than iTerm2)
    CURSOR_TYPE_MAP = {
        0: CursorStyle.BLOCK,
        1: CursorStyle.UNDERLINE,
        2: CursorStyle.BEAM,  # "vertical bar"
    }

    CURSOR_TYPE_REVERSE_MAP = {v: k for k, v in CURSOR_TYPE_MAP.items()}

    # Color key mappings from Terminal.app to CTEC
    COLOR_KEY_MAP = {
        # Core semantic colors
        "TextColor": "foreground",
        "TextBoldColor": "bold",
        "BackgroundColor": "background",
        "CursorColor": "cursor",
        "SelectionColor": "selection",
        # ANSI colors (standard)
        "ANSIBlackColor": "black",
        "ANSIRedColor": "red",
        "ANSIGreenColor": "green",
        "ANSIYellowColor": "yellow",
        "ANSIBlueColor": "blue",
        "ANSIMagentaColor": "magenta",
        "ANSICyanColor": "cyan",
        "ANSIWhiteColor": "white",
        # ANSI colors (bright)
        "ANSIBrightBlackColor": "bright_black",
        "ANSIBrightRedColor": "bright_red",
        "ANSIBrightGreenColor": "bright_green",
        "ANSIBrightYellowColor": "bright_yellow",
        "ANSIBrightBlueColor": "bright_blue",
        "ANSIBrightMagentaColor": "bright_magenta",
        "ANSIBrightCyanColor": "bright_cyan",
        "ANSIBrightWhiteColor": "bright_white",
    }

    COLOR_KEY_REVERSE_MAP = {v: k for k, v in COLOR_KEY_MAP.items()}

    @classmethod
    def can_parse(cls, content: str) -> bool:
        """Check if content looks like a Terminal.app plist config."""
        # Terminal.app uses plist format with specific keys
        if "<!DOCTYPE plist" in content or "<plist" in content:
            terminal_markers = [
                "Window Settings",
                "TextColor",
                "BackgroundColor",
                "ANSIBlackColor",
                "com.apple.Terminal",
            ]
            return any(marker in content for marker in terminal_markers)
        return False

    # Keys to preserve as terminal-specific settings for round-trip conversion
    TERMINAL_SPECIFIC_KEYS = [
        # Profile metadata
        "ProfileCurrentVersion",
        "type",
        "name",
        # Text rendering
        "UseBrightBold",
        "DisableANSIColor",
        "BlinkText",
        # Input/output
        "keyMapBoundKeys",
        "DeleteSendsBackspace",
        "UseOptionAsMetaKey",
        "ScrollAlternateScreen",
        # Session behavior
        "shellExitAction",
        "RunCommandAsShell",
        "CommandString",
        # Encoding
        "StringEncoding",
        # Window appearance
        "ShowWindowSettingsNameInTitle",
        "ShowRepresentedURLInTitle",
        "ShowRepresentedURLPathInTitle",
        "ShowActiveProcessInTitle",
        "ShowActiveProcessArgumentsInTitle",
        "ShowShellCommandInTitle",
        "ShowCommandKeyInTitle",
        "ShowDimensionsInTitle",
        "ShowTTYNameInTitle",
        # Tab behavior
        "ShowActivityIndicatorInTab",
        "ShowTabCloseButton",
    ]

    @classmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
        profile_name: str | None = None,
    ) -> CTEC:
        """
        Parse a Terminal.app configuration file into CTEC format.

        Args:
            source: Path to .terminal file or com.apple.Terminal.plist
            content: Optional string content (if provided, source is used as identifier)
            profile_name: Optional profile name for multi-profile plists

        Returns:
            CTEC configuration

        Raises:
            FileNotFoundError: If the source file doesn't exist
            ValueError: If the configuration cannot be parsed or profile not found
        """
        ctec = CTEC(source_terminal="terminal_app")

        # Load plist data
        if content is not None:
            data = plistlib.loads(content.encode())
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {path}")
            with open(path, "rb") as f:
                data = plistlib.load(f)

        # Detect format: full plist with "Window Settings" or single .terminal profile
        if "Window Settings" in data:
            # Full com.apple.Terminal.plist with multiple profiles
            profiles = data["Window Settings"]

            if not profiles:
                raise ValueError("No profiles found in Terminal.app configuration")

            profile_names = list(profiles.keys())

            if profile_name:
                # User specified a profile
                if profile_name not in profiles:
                    raise ValueError(
                        f"Profile '{profile_name}' not found. "
                        f"Available profiles: {', '.join(profile_names)}"
                    )
                profile_data = profiles[profile_name]
                selected_name = profile_name
            else:
                # Use default profile
                default_name = data.get("Default Window Settings", "Basic")
                if default_name in profiles:
                    profile_data = profiles[default_name]
                    selected_name = default_name
                else:
                    # Fall back to first profile
                    selected_name = profile_names[0]
                    profile_data = profiles[selected_name]

                # Warn about multiple profiles
                if len(profiles) > 1:
                    other_profiles = [n for n in profile_names if n != selected_name]
                    ctec.add_warning(
                        f"Terminal.app config contains {len(profiles)} profiles. "
                        f"Importing '{selected_name}'. "
                        f"Other available profiles: {', '.join(other_profiles)}. "
                        "Use --profile to select a specific profile."
                    )

            cls._parse_profile(profile_data, ctec)
        else:
            # Single .terminal export file (profile is the root)
            cls._parse_profile(data, ctec)

        return ctec

    @classmethod
    def _parse_profile(cls, profile: dict, ctec: CTEC) -> None:
        """
        Parse a single Terminal.app profile into CTEC.

        Args:
            profile: Profile dictionary from plist
            ctec: CTEC object to populate
        """
        # Parse colors
        ctec.color_scheme = cls._parse_color_scheme(profile)

        # Parse font
        ctec.font = cls._parse_font(profile)

        # Parse cursor
        ctec.cursor = cls._parse_cursor(profile)

        # Parse window settings
        ctec.window = cls._parse_window(profile)

        # Parse behavior
        ctec.behavior = cls._parse_behavior(profile)

        # Parse scroll settings
        ctec.scroll = cls._parse_scroll(profile)

        # Store terminal-specific settings for round-trip
        for key in cls.TERMINAL_SPECIFIC_KEYS:
            if key in profile:
                ctec.add_terminal_specific("terminal_app", key, profile[key])

    @classmethod
    def _parse_color_scheme(cls, profile: dict) -> ColorScheme | None:
        """Parse color scheme from profile."""
        scheme = ColorScheme()
        has_colors = False

        for term_key, ctec_key in cls.COLOR_KEY_MAP.items():
            if term_key in profile:
                color_data = profile[term_key]
                if isinstance(color_data, bytes):
                    color = decode_nscolor_data(color_data)
                    if color:
                        setattr(scheme, ctec_key, color)
                        has_colors = True

        return scheme if has_colors else None

    @classmethod
    def _parse_font(cls, profile: dict) -> FontConfig | None:
        """Parse font configuration from profile."""
        font = FontConfig()
        has_font = False

        # Parse main font (NSData)
        if "Font" in profile:
            font_data = profile["Font"]
            if isinstance(font_data, bytes):
                result = decode_nsfont_data(font_data)
                if result:
                    font_name, size = result
                    # Convert PostScript names to friendly names for CTEC
                    if is_postscript_name(font_name):
                        font.family = postscript_to_friendly(font_name)
                        font.set_source_name("terminal_app", font_name)
                    else:
                        font.family = font_name
                    font.size = size
                    has_font = True

        # Parse font anti-aliasing
        if "FontAntialias" in profile:
            font.anti_aliasing = bool(profile["FontAntialias"])
            has_font = True

        # Parse font smoothing (maps to anti_aliasing)
        if "UseFontSmoothing" in profile and font.anti_aliasing is None:
            font.anti_aliasing = bool(profile["UseFontSmoothing"])
            has_font = True

        return font if has_font else None

    @classmethod
    def _parse_cursor(cls, profile: dict) -> CursorConfig | None:
        """Parse cursor configuration from profile."""
        cursor = CursorConfig()
        has_cursor = False

        # Cursor type
        if "CursorType" in profile:
            cursor_type = profile["CursorType"]
            cursor.style = cls.CURSOR_TYPE_MAP.get(cursor_type, CursorStyle.BLOCK)
            has_cursor = True

        # Cursor blink
        if "CursorBlink" in profile:
            cursor.blink = bool(profile["CursorBlink"])
            has_cursor = True

        return cursor if has_cursor else None

    @classmethod
    def _parse_window(cls, profile: dict) -> WindowConfig | None:
        """Parse window configuration from profile."""
        window = WindowConfig()
        has_window = False

        # Window dimensions
        if "columnCount" in profile:
            window.columns = int(profile["columnCount"])
            has_window = True

        if "rowCount" in profile:
            window.rows = int(profile["rowCount"])
            has_window = True

        # Background opacity (Terminal.app uses 0-1 where 1 is opaque)
        if "BackgroundAlpha" in profile:
            window.opacity = float(profile["BackgroundAlpha"])
            has_window = True

        # Background blur
        if "BackgroundBlur" in profile:
            blur_value = profile["BackgroundBlur"]
            # Terminal.app blur is 0-1, convert to radius-like value
            if isinstance(blur_value, (int, float)) and blur_value > 0:
                window.blur = int(blur_value * 20)  # Approximate conversion
                has_window = True

        return window if has_window else None

    @classmethod
    def _parse_behavior(cls, profile: dict) -> BehaviorConfig | None:
        """Parse behavior configuration from profile."""
        behavior = BehaviorConfig()
        has_behavior = False

        # Shell command
        if "CommandString" in profile:
            behavior.shell = profile["CommandString"]
            has_behavior = True

        # Bell mode
        visual_bell = profile.get("VisualBell", False)
        audible_bell = profile.get("BellIsAudible", True)

        if visual_bell:
            behavior.bell_mode = BellMode.VISUAL
            has_behavior = True
        elif not audible_bell:
            behavior.bell_mode = BellMode.NONE
            has_behavior = True
        else:
            behavior.bell_mode = BellMode.AUDIBLE
            has_behavior = True

        return behavior if has_behavior else None

    @classmethod
    def _parse_scroll(cls, profile: dict) -> ScrollConfig | None:
        """Parse scroll configuration from profile."""
        scroll = ScrollConfig()
        has_scroll = False

        # Scrollback lines
        if "ScrollbackLines" in profile:
            lines = int(profile["ScrollbackLines"])
            if lines == 0:
                scroll.disabled = True
            elif lines >= 100000:
                scroll.unlimited = True
            else:
                scroll.lines = lines
            has_scroll = True

        # Unlimited scrollback flag (some versions)
        if "UnlimitedScrollback" in profile:
            if profile["UnlimitedScrollback"]:
                scroll.unlimited = True
                has_scroll = True

        return scroll if has_scroll else None

    @classmethod
    def export(cls, ctec: CTEC) -> str:
        """
        Export CTEC configuration to Terminal.app .terminal format.

        Creates a single profile plist that can be imported into Terminal.app
        via Preferences > Profiles > (gear icon) > Import.

        Args:
            ctec: CTEC configuration to export

        Returns:
            String in Terminal.app plist XML format
        """
        profile = cls._export_profile(ctec)
        return plistlib.dumps(profile).decode("utf-8")

    @classmethod
    def _export_profile(cls, ctec: CTEC) -> dict:
        """
        Export CTEC to a Terminal.app profile dictionary.

        Args:
            ctec: CTEC configuration

        Returns:
            Profile dictionary suitable for plist serialization
        """
        # Determine profile name from terminal-specific settings or use default
        profile_name = "Console Cowboy"
        for setting in ctec.get_terminal_specific("terminal_app"):
            if setting.key == "name":
                profile_name = setting.value
                break

        result = {
            "name": profile_name,
            "type": "Window Settings",
            "ProfileCurrentVersion": 2.07,
        }

        # Export colors
        if ctec.color_scheme:
            cls._export_colors(ctec.color_scheme, result)

        # Export font
        if ctec.font:
            cls._export_font(ctec.font, result)

        # Export cursor
        if ctec.cursor:
            cls._export_cursor(ctec.cursor, result)

        # Export window
        if ctec.window:
            cls._export_window(ctec.window, result)

        # Export behavior
        if ctec.behavior:
            cls._export_behavior(ctec.behavior, result)

        # Export scroll
        if ctec.scroll:
            cls._export_scroll(ctec.scroll, result)

        # Restore terminal-specific settings
        for setting in ctec.get_terminal_specific("terminal_app"):
            # Don't overwrite settings we already set
            if setting.key not in result:
                result[setting.key] = setting.value

        return result

    @classmethod
    def _export_colors(cls, scheme: ColorScheme, result: dict) -> None:
        """Export color scheme to profile dictionary."""
        for ctec_key, term_key in cls.COLOR_KEY_REVERSE_MAP.items():
            color = getattr(scheme, ctec_key, None)
            if color:
                color_data = encode_nscolor_data(color)
                if color_data:
                    result[term_key] = color_data

    @classmethod
    def _export_font(cls, font: FontConfig, result: dict) -> None:
        """Export font configuration to profile dictionary."""
        if font.family and font.size:
            # Terminal.app's NSFont works best with PostScript names
            # Try to get original PostScript name from source, or convert
            font_name = None

            # Check for stored source name (PostScript format)
            if font._source_names:
                # Prefer terminal_app source, then any other
                font_name = font._source_names.get("terminal_app")
                if not font_name:
                    # Use first available source name
                    font_name = next(iter(font._source_names.values()), None)

            # Fall back to converting friendly name to PostScript
            if not font_name:
                font_name = friendly_to_postscript(font.family)

            font_data = encode_nsfont_data(font_name, font.size)
            if font_data:
                result["Font"] = font_data

        if font.anti_aliasing is not None:
            result["FontAntialias"] = font.anti_aliasing
            result["UseFontSmoothing"] = font.anti_aliasing

    @classmethod
    def _export_cursor(cls, cursor: CursorConfig, result: dict) -> None:
        """Export cursor configuration to profile dictionary."""
        if cursor.style:
            result["CursorType"] = cls.CURSOR_TYPE_REVERSE_MAP.get(
                cursor.style,
                0,  # Default to BLOCK
            )

        if cursor.blink is not None:
            result["CursorBlink"] = cursor.blink

    @classmethod
    def _export_window(cls, window: WindowConfig, result: dict) -> None:
        """Export window configuration to profile dictionary."""
        if window.columns is not None:
            result["columnCount"] = window.columns

        if window.rows is not None:
            result["rowCount"] = window.rows

        if window.opacity is not None:
            result["BackgroundAlpha"] = window.opacity

        if window.blur is not None and window.blur > 0:
            # Convert radius-like value back to 0-1 range
            result["BackgroundBlur"] = min(1.0, window.blur / 20.0)

    @classmethod
    def _export_behavior(cls, behavior: BehaviorConfig, result: dict) -> None:
        """Export behavior configuration to profile dictionary."""
        if behavior.shell:
            result["CommandString"] = behavior.shell
            result["RunCommandAsShell"] = True

        if behavior.bell_mode:
            if behavior.bell_mode == BellMode.VISUAL:
                result["VisualBell"] = True
                result["BellIsAudible"] = False
            elif behavior.bell_mode == BellMode.NONE:
                result["VisualBell"] = False
                result["BellIsAudible"] = False
            else:  # AUDIBLE
                result["VisualBell"] = False
                result["BellIsAudible"] = True

    @classmethod
    def _export_scroll(cls, scroll: ScrollConfig, result: dict) -> None:
        """Export scroll configuration to profile dictionary."""
        if scroll.unlimited:
            result["ScrollbackLines"] = 0
            result["UnlimitedScrollback"] = True
        elif scroll.disabled:
            result["ScrollbackLines"] = 0
            result["UnlimitedScrollback"] = False
        elif scroll.lines is not None:
            result["ScrollbackLines"] = scroll.lines
            result["UnlimitedScrollback"] = False
