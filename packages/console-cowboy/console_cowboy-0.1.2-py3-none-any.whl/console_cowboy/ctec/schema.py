"""
CTEC Schema - Data model for Common Terminal Emulator Configuration.

This module defines the portable configuration format that serves as an
intermediate representation for terminal emulator settings.
"""

from dataclasses import dataclass, field
from enum import Enum


class CursorStyle(Enum):
    """Cursor appearance styles supported by most terminal emulators."""

    BLOCK = "block"
    BEAM = "beam"
    UNDERLINE = "underline"


class BellMode(Enum):
    """Bell notification modes."""

    NONE = "none"
    AUDIBLE = "audible"
    VISUAL = "visual"


class ColorVariant(Enum):
    """Color scheme variant (light or dark theme)."""

    DARK = "dark"
    LIGHT = "light"


class FontWeight(Enum):
    """Standard font weights (CSS-style numeric values)."""

    THIN = 100
    EXTRA_LIGHT = 200
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMI_BOLD = 600
    BOLD = 700
    EXTRA_BOLD = 800
    BLACK = 900

    @classmethod
    def from_string(cls, name: str) -> "FontWeight":
        """Convert a weight name string to FontWeight."""
        # Try numeric lookup first
        try:
            numeric = int(name)
            for member in cls:
                if member.value == numeric:
                    return member
            raise ValueError(f"Unknown numeric weight: {name}")
        except ValueError:
            pass

        name_map = {
            "thin": cls.THIN,
            "extralight": cls.EXTRA_LIGHT,
            "extra-light": cls.EXTRA_LIGHT,
            "ultralight": cls.EXTRA_LIGHT,
            "light": cls.LIGHT,
            "regular": cls.REGULAR,
            "normal": cls.REGULAR,
            "medium": cls.MEDIUM,
            "semibold": cls.SEMI_BOLD,
            "semi-bold": cls.SEMI_BOLD,
            "demibold": cls.SEMI_BOLD,
            "bold": cls.BOLD,
            "extrabold": cls.EXTRA_BOLD,
            "extra-bold": cls.EXTRA_BOLD,
            "ultrabold": cls.EXTRA_BOLD,
            "black": cls.BLACK,
            "heavy": cls.BLACK,
        }
        result = name_map.get(name.lower().replace(" ", ""))
        if result is None:
            raise ValueError(f"Unknown font weight: {name}")
        return result

    def to_string(self) -> str:
        """Convert to human-readable weight name."""
        name_map = {
            FontWeight.THIN: "Thin",
            FontWeight.EXTRA_LIGHT: "ExtraLight",
            FontWeight.LIGHT: "Light",
            FontWeight.REGULAR: "Regular",
            FontWeight.MEDIUM: "Medium",
            FontWeight.SEMI_BOLD: "SemiBold",
            FontWeight.BOLD: "Bold",
            FontWeight.EXTRA_BOLD: "ExtraBold",
            FontWeight.BLACK: "Black",
        }
        return name_map.get(self, "Regular")


class FontStyle(Enum):
    """Font style variants."""

    NORMAL = "normal"
    ITALIC = "italic"
    OBLIQUE = "oblique"


class QuickTerminalPosition(Enum):
    """
    Position where the quick terminal appears on screen.

    Common across terminals:
    - Ghostty: quick-terminal-position (top, bottom, left, right)
    - iTerm2: Hotkey Window Type (0=floating, 1=fullscreen, 2=left, 3=right, 4=bottom, 5=top)
    - Kitty: edge option (top, bottom, left, right, background)
    """

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    # iTerm2-specific: floating window (not docked to edge)
    FLOATING = "floating"
    # iTerm2-specific: full screen
    FULLSCREEN = "fullscreen"
    # Kitty-specific: use as desktop background
    BACKGROUND = "background"


class QuickTerminalScreen(Enum):
    """
    Which screen/monitor the quick terminal appears on.

    Common across terminals:
    - Ghostty: quick-terminal-screen (main, mouse, macos-menu-bar)
    - iTerm2: Screen with Selection (uses current screen by default)
    """

    # Primary/main display
    MAIN = "main"
    # Screen where mouse cursor is located
    MOUSE = "mouse"
    # macOS menu bar screen (Ghostty-specific)
    MACOS_MENU_BAR = "macos-menu-bar"
    # Use all screens (for background mode in Kitty)
    ALL = "all"


@dataclass
class Color:
    """
    Represents an RGB color.

    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for component, name in [(self.r, "r"), (self.g, "g"), (self.b, "b")]:
            if not 0 <= component <= 255:
                raise ValueError(
                    f"Color component {name} must be 0-255, got {component}"
                )

    def to_hex(self) -> str:
        """Convert to hex color string (e.g., '#ff0000')."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create a Color from a hex string (e.g., '#ff0000' or 'ff0000')."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        return cls(
            r=int(hex_str[0:2], 16),
            g=int(hex_str[2:4], 16),
            b=int(hex_str[4:6], 16),
        )

    def to_dict(self) -> str:
        """Convert to hex string for serialization (iTerm2-Color-Schemes format)."""
        return self.to_hex()

    @classmethod
    def from_dict(cls, data: "str | dict") -> "Color":
        """Create a Color from serialized data.

        Accepts both:
        - Hex string: "#ff0000" (iTerm2-Color-Schemes format)
        - RGB dict: {"r": 255, "g": 0, "b": 0} (legacy format)
        """
        if isinstance(data, str):
            return cls.from_hex(data)
        return cls(r=data["r"], g=data["g"], b=data["b"])


@dataclass
class ColorScheme:
    """
    Terminal color scheme with ANSI colors and semantic colors.

    This schema is designed to align with the iTerm2-Color-Schemes extended YAML
    format, which has become the de facto standard for terminal color scheme
    interchange. See: https://github.com/mbadolato/iTerm2-Color-Schemes

    Attributes:
        name: Optional name for the color scheme
        author: Optional author attribution
        variant: Theme variant (dark or light)

        # Core semantic colors (from Gogh base format)
        foreground: Default text color
        background: Default background color
        cursor: Cursor color

        # Extended semantic colors (from iTerm2-Color-Schemes YAML)
        cursor_text: Text color when under cursor (default: foreground)
        selection: Selection highlight color (default: foreground)
        selection_text: Selected text color (default: background)
        bold: Bold text color (default: foreground)
        link: Hyperlink/URL color
        underline: Underlined text color
        cursor_guide: Cursor guide/highlight color (default: cursor)

        # ANSI colors 0-7 (normal)
        black, red, green, yellow, blue, magenta, cyan, white

        # ANSI colors 8-15 (bright)
        bright_black, bright_red, bright_green, bright_yellow,
        bright_blue, bright_magenta, bright_cyan, bright_white
    """

    # Metadata
    name: str | None = None
    author: str | None = None
    variant: ColorVariant | None = None

    # Core semantic colors (Gogh base format)
    foreground: Color | None = None
    background: Color | None = None
    cursor: Color | None = None

    # Extended semantic colors (iTerm2-Color-Schemes YAML extensions)
    cursor_text: Color | None = None
    selection: Color | None = None
    selection_text: Color | None = None
    bold: Color | None = None
    link: Color | None = None
    underline: Color | None = None
    cursor_guide: Color | None = None

    # Normal colors (0-7)
    black: Color | None = None
    red: Color | None = None
    green: Color | None = None
    yellow: Color | None = None
    blue: Color | None = None
    magenta: Color | None = None
    cyan: Color | None = None
    white: Color | None = None

    # Bright colors (8-15)
    bright_black: Color | None = None
    bright_red: Color | None = None
    bright_green: Color | None = None
    bright_yellow: Color | None = None
    bright_blue: Color | None = None
    bright_magenta: Color | None = None
    bright_cyan: Color | None = None
    bright_white: Color | None = None

    # All color field names for iteration
    _COLOR_FIELDS = [
        "foreground",
        "background",
        "cursor",
        "cursor_text",
        "selection",
        "selection_text",
        "bold",
        "link",
        "underline",
        "cursor_guide",
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

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        # Metadata fields
        if self.name is not None:
            result["name"] = self.name
        if self.author is not None:
            result["author"] = self.author
        if self.variant is not None:
            result["variant"] = self.variant.value
        # Color fields
        for field_name in self._COLOR_FIELDS:
            color = getattr(self, field_name)
            if color is not None:
                result[field_name] = color.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ColorScheme":
        """Create a ColorScheme from a dictionary."""
        kwargs = {}
        # Metadata fields
        if "name" in data:
            kwargs["name"] = data["name"]
        if "author" in data:
            kwargs["author"] = data["author"]
        if "variant" in data:
            kwargs["variant"] = ColorVariant(data["variant"])
        # Color fields
        for field_name in cls._COLOR_FIELDS:
            if field_name in data:
                kwargs[field_name] = Color.from_dict(data[field_name])
        return cls(**kwargs)


@dataclass
class FontConfig:
    """
    Font configuration for the terminal.

    Design Principles:
    - Store friendly names as the canonical format (most human-readable)
    - Resolve to PostScript names on export when needed (iTerm2)
    - Preserve original names in _source_names for lossless round-trips

    Attributes:
        family: Primary font family name (friendly format, e.g., 'JetBrains Mono')
        size: Font size in points
        line_height: Line height multiplier (1.0 = normal)
        cell_width: Character cell width multiplier (1.0 = normal)
        weight: Font weight for normal text (Regular, Bold, etc.)
        style: Font style for normal text (Normal, Italic, Oblique)
        bold_font: Optional separate font family for bold text
        italic_font: Optional separate font family for italic text
        bold_italic_font: Optional separate font family for bold italic text
        ligatures: Whether to enable font ligatures
        anti_aliasing: Whether to enable anti-aliasing (macOS/iTerm2 specific)
        fallback_fonts: List of fallback font families in priority order
        symbol_map: Map of unicode ranges to font families (e.g., for Nerd Fonts)
                    Format: {"U+E000-U+F8FF": "Symbols Nerd Font"}
        draw_powerline_glyphs: Use built-in Powerline glyph rendering (iTerm2)
        box_drawing_scale: Scale factor for box drawing characters
        _source_names: Original font names from source terminal (for round-trip)
    """

    family: str | None = None
    size: float | None = None
    line_height: float | None = None
    cell_width: float | None = None
    weight: FontWeight | None = None
    style: FontStyle | None = None
    bold_font: str | None = None
    italic_font: str | None = None
    bold_italic_font: str | None = None
    ligatures: bool | None = None
    anti_aliasing: bool | None = None
    fallback_fonts: list[str] | None = None
    symbol_map: dict[str, str] | None = None
    draw_powerline_glyphs: bool | None = None
    box_drawing_scale: float | None = None
    # Internal: preserve original names for lossless round-trips
    _source_names: dict[str, str] | None = field(default=None, repr=False)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        # Simple fields
        for field_name in [
            "family",
            "size",
            "line_height",
            "cell_width",
            "bold_font",
            "italic_font",
            "bold_italic_font",
            "ligatures",
            "anti_aliasing",
            "draw_powerline_glyphs",
            "box_drawing_scale",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        # Enum fields - use string names for readability
        if self.weight is not None:
            result["weight"] = self.weight.to_string().lower()
        if self.style is not None:
            result["style"] = self.style.value
        # List fields
        if self.fallback_fonts:
            result["fallback_fonts"] = self.fallback_fonts
        # Dict fields
        if self.symbol_map:
            result["symbol_map"] = self.symbol_map
        # Source names for round-trip (only if present)
        if self._source_names:
            result["_source_names"] = self._source_names
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "FontConfig":
        """Create a FontConfig from a dictionary."""
        weight = None
        if "weight" in data:
            # Support both string names and numeric values
            weight_val = data["weight"]
            if isinstance(weight_val, int):
                weight = FontWeight(weight_val)
            else:
                weight = FontWeight.from_string(str(weight_val))

        return cls(
            family=data.get("family"),
            size=data.get("size"),
            line_height=data.get("line_height"),
            cell_width=data.get("cell_width"),
            weight=weight,
            style=FontStyle(data["style"]) if "style" in data else None,
            bold_font=data.get("bold_font"),
            italic_font=data.get("italic_font"),
            bold_italic_font=data.get("bold_italic_font"),
            ligatures=data.get("ligatures"),
            anti_aliasing=data.get("anti_aliasing"),
            fallback_fonts=data.get("fallback_fonts"),
            symbol_map=data.get("symbol_map"),
            draw_powerline_glyphs=data.get("draw_powerline_glyphs"),
            box_drawing_scale=data.get("box_drawing_scale"),
            _source_names=data.get("_source_names"),
        )

    def set_source_name(self, terminal: str, name: str) -> None:
        """Store the original font name from a specific terminal for round-trip."""
        if self._source_names is None:
            self._source_names = {}
        self._source_names[terminal] = name

    def get_source_name(self, terminal: str) -> str | None:
        """Get the original font name for a specific terminal."""
        if self._source_names is None:
            return None
        return self._source_names.get(terminal)


@dataclass
class CursorConfig:
    """
    Cursor appearance and behavior configuration.

    Attributes:
        style: Cursor shape (block, beam, or underline)
        blink: Whether the cursor should blink
        blink_interval: Blink interval in milliseconds
    """

    style: CursorStyle | None = None
    blink: bool | None = None
    blink_interval: int | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        if self.style is not None:
            result["style"] = self.style.value
        if self.blink is not None:
            result["blink"] = self.blink
        if self.blink_interval is not None:
            result["blink_interval"] = self.blink_interval
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CursorConfig":
        """Create a CursorConfig from a dictionary."""
        return cls(
            style=CursorStyle(data["style"]) if "style" in data else None,
            blink=data.get("blink"),
            blink_interval=data.get("blink_interval"),
        )


@dataclass
class WindowConfig:
    """
    Window appearance and behavior configuration.

    Attributes:
        columns: Initial number of columns
        rows: Initial number of rows
        opacity: Window opacity (0.0 = transparent, 1.0 = opaque)
        blur: Background blur radius (0 = no blur)
        padding_horizontal: Horizontal padding in pixels
        padding_vertical: Vertical padding in pixels
        decorations: Whether to show window decorations (title bar, etc.)
        startup_mode: Initial window mode ('windowed', 'maximized', 'fullscreen')
        dynamic_title: Whether to update window title from shell
    """

    columns: int | None = None
    rows: int | None = None
    opacity: float | None = None
    blur: int | None = None
    padding_horizontal: int | None = None
    padding_vertical: int | None = None
    decorations: bool | None = None
    startup_mode: str | None = None
    dynamic_title: bool | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        for field_name in [
            "columns",
            "rows",
            "opacity",
            "blur",
            "padding_horizontal",
            "padding_vertical",
            "decorations",
            "startup_mode",
            "dynamic_title",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "WindowConfig":
        """Create a WindowConfig from a dictionary."""
        return cls(
            columns=data.get("columns"),
            rows=data.get("rows"),
            opacity=data.get("opacity"),
            blur=data.get("blur"),
            padding_horizontal=data.get("padding_horizontal"),
            padding_vertical=data.get("padding_vertical"),
            decorations=data.get("decorations"),
            startup_mode=data.get("startup_mode"),
            dynamic_title=data.get("dynamic_title"),
        )


@dataclass
class ScrollConfig:
    """
    Scrollback buffer and scroll behavior configuration.

    Provides an implementation-agnostic representation of scrolling that
    maps losslessly to terminal-specific settings. Different terminals use
    different units (lines vs bytes) and have different capabilities
    (unlimited vs capped).

    Capacity Semantics (mutually exclusive, checked in priority order):
    1. disabled=True: Explicitly disable scrollback (maps to 0 everywhere)
    2. unlimited=True: Maximum scrollback (maps to iTerm2 "Unlimited Scrollback",
       Kitty -1, or max safe values for terminals without unlimited support)
    3. lines set: Specific line count (converted to bytes for Ghostty using
       an estimated ~100 bytes per line)

    If none are set, the terminal's default is used.

    Terminal Defaults:
    - iTerm2: 1000 lines (or unlimited if checkbox enabled)
    - Ghostty: 10MB (~100,000 lines equivalent)
    - Alacritty: 10,000 lines (max 100,000)
    - Kitty: 2,000 lines (-1 for unlimited)
    - Wezterm: 3,500 lines

    Attributes:
        unlimited: User wants maximum possible scrollback history
        disabled: User explicitly wants no scrollback (security/memory)
        lines: Specific number of lines to keep in scrollback buffer
        multiplier: Scroll speed multiplier (1.0 = normal, higher = faster)
    """

    unlimited: bool | None = None
    disabled: bool | None = None
    lines: int | None = None
    multiplier: float | None = None

    def get_effective_lines(self, default: int = 10000, max_lines: int = 100000) -> int:
        """
        Get the effective line count for terminals that use line-based scrollback.

        Args:
            default: Default line count if nothing specified
            max_lines: Maximum supported lines (for unlimited mode)

        Returns:
            Line count to use, or 0 if disabled
        """
        if self.disabled:
            return 0
        if self.unlimited:
            return max_lines
        if self.lines is not None:
            return min(self.lines, max_lines)
        return default

    def get_effective_bytes(self, default_bytes: int = 10485760) -> int:
        """
        Get the effective byte count for terminals that use byte-based scrollback.

        Uses an estimate of ~100 bytes per line for conversion.

        Args:
            default_bytes: Default byte count if nothing specified (10MB)

        Returns:
            Byte count to use, or 0 if disabled
        """
        bytes_per_line = 100  # Conservative estimate for average line

        if self.disabled:
            return 0
        if self.unlimited:
            # Ghostty max is u32::MAX, but 100MB is practical
            return 104857600  # 100MB
        if self.lines is not None:
            return self.lines * bytes_per_line
        return default_bytes

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        if self.unlimited is not None:
            result["unlimited"] = self.unlimited
        if self.disabled is not None:
            result["disabled"] = self.disabled
        if self.lines is not None:
            result["lines"] = self.lines
        if self.multiplier is not None:
            result["multiplier"] = self.multiplier
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "ScrollConfig":
        """Create a ScrollConfig from a dictionary."""
        return cls(
            unlimited=data.get("unlimited"),
            disabled=data.get("disabled"),
            lines=data.get("lines"),
            multiplier=data.get("multiplier"),
        )

    @classmethod
    def from_lines(cls, lines: int) -> "ScrollConfig":
        """Create a ScrollConfig from a line count.

        Handles special values:
        - Negative values: treated as unlimited
        - Zero: treated as disabled
        - Positive: specific line count
        """
        if lines < 0:
            return cls(unlimited=True)
        elif lines == 0:
            return cls(disabled=True)
        else:
            return cls(lines=lines)

    @classmethod
    def from_bytes(cls, byte_count: int, bytes_per_line: int = 100) -> "ScrollConfig":
        """Create a ScrollConfig from a byte count (for Ghostty).

        Args:
            byte_count: Scrollback limit in bytes
            bytes_per_line: Estimated bytes per line for conversion
        """
        if byte_count == 0:
            return cls(disabled=True)
        # Convert bytes to approximate lines
        lines = byte_count // bytes_per_line
        # If it's a very large value (>1M lines), treat as unlimited
        if lines > 1000000:
            return cls(unlimited=True)
        return cls(lines=lines)


@dataclass
class BehaviorConfig:
    """
    Terminal behavior configuration.

    Attributes:
        shell: Shell command or path to execute
        working_directory: Initial working directory
        scrollback_lines: DEPRECATED - use CTEC.scroll instead
        mouse_enabled: Whether to enable mouse support
        bell_mode: Bell notification mode
        copy_on_select: Whether to copy text to clipboard on selection
        confirm_close: Whether to confirm before closing with running processes
        close_on_exit: Action when shell exits ('close', 'hold', 'restart')
    """

    shell: str | None = None
    working_directory: str | None = None
    scrollback_lines: int | None = None  # DEPRECATED: use CTEC.scroll
    mouse_enabled: bool | None = None
    bell_mode: BellMode | None = None
    copy_on_select: bool | None = None
    confirm_close: bool | None = None
    close_on_exit: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        for field_name in [
            "shell",
            "working_directory",
            "scrollback_lines",
            "mouse_enabled",
            "copy_on_select",
            "confirm_close",
            "close_on_exit",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        if self.bell_mode is not None:
            result["bell_mode"] = self.bell_mode.value
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "BehaviorConfig":
        """Create a BehaviorConfig from a dictionary."""
        return cls(
            shell=data.get("shell"),
            working_directory=data.get("working_directory"),
            scrollback_lines=data.get("scrollback_lines"),
            mouse_enabled=data.get("mouse_enabled"),
            bell_mode=BellMode(data["bell_mode"]) if "bell_mode" in data else None,
            copy_on_select=data.get("copy_on_select"),
            confirm_close=data.get("confirm_close"),
            close_on_exit=data.get("close_on_exit"),
        )


@dataclass
class KeyBinding:
    """
    A keyboard shortcut binding.

    Attributes:
        action: The action to perform (e.g., 'copy', 'paste', 'new_tab')
        key: The key (e.g., 'c', 'v', 'Return')
        mods: Modifier keys (e.g., ['ctrl'], ['ctrl', 'shift'])
    """

    action: str
    key: str
    mods: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {"action": self.action, "key": self.key}
        if self.mods:
            result["mods"] = self.mods
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "KeyBinding":
        """Create a KeyBinding from a dictionary."""
        return cls(
            action=data["action"],
            key=data["key"],
            mods=data.get("mods", []),
        )


@dataclass
class QuickTerminalConfig:
    """
    Configuration for quake-style/dropdown quick terminal functionality.

    This is a cross-terminal representation of the "quick terminal" or "hotkey window"
    feature that allows summoning a terminal with a global hotkey, typically sliding
    in from a screen edge.

    Terminal Support:
    - iTerm2: Hotkey Window profiles with Has Hotkey, Hotkey Key Code, etc.
    - Ghostty: quick-terminal-* settings (quick-terminal-position, etc.)
    - Kitty 0.42+: quick-access-terminal kitten with edge, hide_on_focus_loss, etc.
    - Alacritty: No native support (requires external tools like tdrop)
    - WezTerm: No native support (requires external tools)

    Attributes:
        enabled: Whether this profile/config is a quick terminal
        position: Which screen edge the terminal appears from
        screen: Which monitor/screen to use
        animation_duration: Animation duration in milliseconds (0 = instant)
        opacity: Override opacity for quick terminal (0.0-1.0, None = use default)
        hide_on_focus_loss: Auto-hide when terminal loses keyboard focus
        floating: Whether window floats above other windows (iTerm2)
        hotkey: The hotkey trigger as a string (e.g., "ctrl+`", "F12")
        hotkey_key_code: Raw key code for the hotkey (iTerm2)
        hotkey_modifiers: Modifier flags as integer bitmask (iTerm2)
        size_percent: Size as percentage of screen (height for top/bottom, width for left/right)
    """

    enabled: bool | None = None
    position: QuickTerminalPosition | None = None
    screen: QuickTerminalScreen | None = None
    animation_duration: int | None = None  # milliseconds
    opacity: float | None = None
    hide_on_focus_loss: bool | None = None
    floating: bool | None = None
    hotkey: str | None = None
    hotkey_key_code: int | None = None
    hotkey_modifiers: int | None = None
    size_percent: float | None = None  # e.g., 0.5 = 50% of screen

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {}
        for field_name in [
            "enabled",
            "animation_duration",
            "opacity",
            "hide_on_focus_loss",
            "floating",
            "hotkey",
            "hotkey_key_code",
            "hotkey_modifiers",
            "size_percent",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        if self.position is not None:
            result["position"] = self.position.value
        if self.screen is not None:
            result["screen"] = self.screen.value
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "QuickTerminalConfig":
        """Create a QuickTerminalConfig from a dictionary."""
        return cls(
            enabled=data.get("enabled"),
            position=QuickTerminalPosition(data["position"])
            if "position" in data
            else None,
            screen=QuickTerminalScreen(data["screen"]) if "screen" in data else None,
            animation_duration=data.get("animation_duration"),
            opacity=data.get("opacity"),
            hide_on_focus_loss=data.get("hide_on_focus_loss"),
            floating=data.get("floating"),
            hotkey=data.get("hotkey"),
            hotkey_key_code=data.get("hotkey_key_code"),
            hotkey_modifiers=data.get("hotkey_modifiers"),
            size_percent=data.get("size_percent"),
        )


@dataclass
class TerminalSpecificSetting:
    """
    A setting specific to a particular terminal emulator that cannot
    be mapped to a common CTEC setting.

    Attributes:
        terminal: Terminal emulator name (e.g., 'iterm2', 'ghostty')
        key: Configuration key path (e.g., 'Unlimited Scrollback')
        value: Configuration value (any serializable type)
    """

    terminal: str
    key: str
    value: object

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {"terminal": self.terminal, "key": self.key, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "TerminalSpecificSetting":
        """Create a TerminalSpecificSetting from a dictionary."""
        return cls(terminal=data["terminal"], key=data["key"], value=data["value"])


@dataclass
class CTEC:
    """
    Common Terminal Emulator Configuration.

    The main container for all portable terminal configuration settings.
    This serves as the intermediate format for converting between different
    terminal emulator configurations.

    Attributes:
        version: CTEC format version
        source_terminal: Original terminal emulator this config was exported from
        color_scheme: Color scheme configuration
        font: Font configuration
        cursor: Cursor configuration
        window: Window configuration
        behavior: Terminal behavior configuration
        scroll: Scrollback and scroll behavior configuration
        quick_terminal: Quick terminal / hotkey window configuration
        key_bindings: List of keyboard shortcuts
        terminal_specific: Settings that cannot be mapped to common CTEC fields
        warnings: Compatibility warnings generated during import/export
    """

    version: str = "1.0"
    source_terminal: str | None = None
    color_scheme: ColorScheme | None = None
    font: FontConfig | None = None
    cursor: CursorConfig | None = None
    window: WindowConfig | None = None
    behavior: BehaviorConfig | None = None
    scroll: ScrollConfig | None = None
    quick_terminal: QuickTerminalConfig | None = None
    key_bindings: list[KeyBinding] = field(default_factory=list)
    terminal_specific: list[TerminalSpecificSetting] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary representation suitable for serialization."""
        result = {"version": self.version}
        if self.source_terminal is not None:
            result["source_terminal"] = self.source_terminal
        if self.color_scheme is not None:
            result["color_scheme"] = self.color_scheme.to_dict()
        if self.font is not None:
            result["font"] = self.font.to_dict()
        if self.cursor is not None:
            result["cursor"] = self.cursor.to_dict()
        if self.window is not None:
            result["window"] = self.window.to_dict()
        if self.behavior is not None:
            result["behavior"] = self.behavior.to_dict()
        if self.scroll is not None:
            result["scroll"] = self.scroll.to_dict()
        if self.quick_terminal is not None:
            result["quick_terminal"] = self.quick_terminal.to_dict()
        if self.key_bindings:
            result["key_bindings"] = [kb.to_dict() for kb in self.key_bindings]
        if self.terminal_specific:
            result["terminal_specific"] = [
                ts.to_dict() for ts in self.terminal_specific
            ]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CTEC":
        """Create a CTEC from a dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            source_terminal=data.get("source_terminal"),
            color_scheme=ColorScheme.from_dict(data["color_scheme"])
            if "color_scheme" in data
            else None,
            font=FontConfig.from_dict(data["font"]) if "font" in data else None,
            cursor=CursorConfig.from_dict(data["cursor"]) if "cursor" in data else None,
            window=WindowConfig.from_dict(data["window"]) if "window" in data else None,
            behavior=BehaviorConfig.from_dict(data["behavior"])
            if "behavior" in data
            else None,
            scroll=ScrollConfig.from_dict(data["scroll"]) if "scroll" in data else None,
            quick_terminal=QuickTerminalConfig.from_dict(data["quick_terminal"])
            if "quick_terminal" in data
            else None,
            key_bindings=[
                KeyBinding.from_dict(kb) for kb in data.get("key_bindings", [])
            ],
            terminal_specific=[
                TerminalSpecificSetting.from_dict(ts)
                for ts in data.get("terminal_specific", [])
            ],
            warnings=data.get("warnings", []),
        )

    def add_warning(self, warning: str) -> None:
        """Add a compatibility warning."""
        self.warnings.append(warning)

    def add_terminal_specific(self, terminal: str, key: str, value: object) -> None:
        """Add a terminal-specific setting."""
        self.terminal_specific.append(
            TerminalSpecificSetting(terminal=terminal, key=key, value=value)
        )

    def get_terminal_specific(self, terminal: str) -> list[TerminalSpecificSetting]:
        """Get all terminal-specific settings for a given terminal."""
        return [ts for ts in self.terminal_specific if ts.terminal == terminal]
