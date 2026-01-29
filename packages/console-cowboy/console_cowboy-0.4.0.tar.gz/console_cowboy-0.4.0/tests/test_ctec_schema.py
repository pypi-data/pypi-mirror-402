"""Tests for CTEC schema and data model."""

import pytest

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
    FontWeight,
    KeyBinding,
    ScrollConfig,
    TerminalSpecificSetting,
    WindowConfig,
)


class TestColor:
    """Tests for the Color class."""

    def test_create_valid_color(self):
        color = Color(r=255, g=128, b=0)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_invalid_color_raises(self):
        with pytest.raises(ValueError):
            Color(r=256, g=0, b=0)
        with pytest.raises(ValueError):
            Color(r=0, g=-1, b=0)

    def test_to_hex(self):
        color = Color(r=255, g=128, b=0)
        assert color.to_hex() == "#ff8000"

    def test_to_hex_with_leading_zeros(self):
        color = Color(r=0, g=15, b=255)
        assert color.to_hex() == "#000fff"

    def test_from_hex_with_hash(self):
        color = Color.from_hex("#ff8000")
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_from_hex_without_hash(self):
        color = Color.from_hex("ff8000")
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_from_hex_short_format(self):
        color = Color.from_hex("#f80")
        assert color.r == 255
        assert color.g == 136
        assert color.b == 0

    def test_from_hex_invalid(self):
        with pytest.raises(ValueError):
            Color.from_hex("invalid")

    def test_to_dict(self):
        """Test that to_dict returns hex string for iTerm2-Color-Schemes format."""
        color = Color(r=255, g=128, b=0)
        assert color.to_dict() == "#ff8000"

    def test_from_dict_hex_string(self):
        """Test from_dict with hex string (iTerm2-Color-Schemes format)."""
        color = Color.from_dict("#ff8000")
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0

    def test_from_dict_rgb_dict(self):
        """Test from_dict with RGB dict (legacy format for backwards compatibility)."""
        color = Color.from_dict({"r": 255, "g": 128, "b": 0})
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0


class TestColorScheme:
    """Tests for the ColorScheme class."""

    def test_empty_scheme(self):
        scheme = ColorScheme()
        assert scheme.foreground is None
        assert scheme.background is None

    def test_scheme_with_colors(self):
        scheme = ColorScheme(
            foreground=Color(255, 255, 255),
            background=Color(0, 0, 0),
        )
        assert scheme.foreground.r == 255
        assert scheme.background.r == 0

    def test_to_dict(self):
        scheme = ColorScheme(
            name="Test",
            foreground=Color(255, 255, 255),
        )
        d = scheme.to_dict()
        assert d["name"] == "Test"
        assert d["foreground"] == "#ffffff"

    def test_from_dict_hex_strings(self):
        """Test from_dict with hex strings (iTerm2-Color-Schemes format)."""
        scheme = ColorScheme.from_dict(
            {
                "name": "Test",
                "foreground": "#ffffff",
            }
        )
        assert scheme.name == "Test"
        assert scheme.foreground.r == 255

    def test_from_dict_rgb_dicts(self):
        """Test from_dict with RGB dicts (legacy format for backwards compatibility)."""
        scheme = ColorScheme.from_dict(
            {
                "name": "Test",
                "foreground": {"r": 255, "g": 255, "b": 255},
            }
        )
        assert scheme.name == "Test"
        assert scheme.foreground.r == 255


class TestFontWeight:
    """Tests for the FontWeight enum."""

    def test_weight_values(self):
        """Test numeric weight values."""
        assert FontWeight.THIN.value == 100
        assert FontWeight.REGULAR.value == 400
        assert FontWeight.BOLD.value == 700
        assert FontWeight.BLACK.value == 900

    def test_from_string_regular(self):
        """Test parsing 'Regular' string."""
        assert FontWeight.from_string("Regular") == FontWeight.REGULAR
        assert FontWeight.from_string("regular") == FontWeight.REGULAR
        assert FontWeight.from_string("Normal") == FontWeight.REGULAR

    def test_from_string_bold(self):
        """Test parsing 'Bold' string."""
        assert FontWeight.from_string("Bold") == FontWeight.BOLD
        assert FontWeight.from_string("bold") == FontWeight.BOLD

    def test_from_string_light(self):
        """Test parsing 'Light' string."""
        assert FontWeight.from_string("Light") == FontWeight.LIGHT

    def test_from_string_semibold(self):
        """Test parsing 'SemiBold' string."""
        assert FontWeight.from_string("SemiBold") == FontWeight.SEMI_BOLD
        assert FontWeight.from_string("Semibold") == FontWeight.SEMI_BOLD
        assert FontWeight.from_string("DemiBold") == FontWeight.SEMI_BOLD

    def test_from_string_numeric(self):
        """Test parsing numeric weight strings."""
        assert FontWeight.from_string("400") == FontWeight.REGULAR
        assert FontWeight.from_string("700") == FontWeight.BOLD

    def test_from_string_invalid(self):
        """Test invalid string raises ValueError."""
        with pytest.raises(ValueError):
            FontWeight.from_string("InvalidWeight")

    def test_to_string(self):
        """Test converting weight to string."""
        assert FontWeight.REGULAR.to_string() == "Regular"
        assert FontWeight.BOLD.to_string() == "Bold"
        assert FontWeight.LIGHT.to_string() == "Light"
        assert FontWeight.SEMI_BOLD.to_string() == "SemiBold"


class TestFontStyle:
    """Tests for the FontStyle enum."""

    def test_style_values(self):
        """Test style values."""
        assert FontStyle.NORMAL.value == "normal"
        assert FontStyle.ITALIC.value == "italic"
        assert FontStyle.OBLIQUE.value == "oblique"


class TestFontConfig:
    """Tests for the FontConfig class."""

    def test_empty_font(self):
        font = FontConfig()
        assert font.family is None
        assert font.size is None

    def test_font_with_values(self):
        font = FontConfig(family="JetBrains Mono", size=14.0, ligatures=True)
        assert font.family == "JetBrains Mono"
        assert font.size == 14.0
        assert font.ligatures is True

    def test_to_dict(self):
        font = FontConfig(family="Fira Code", size=12.0)
        d = font.to_dict()
        assert d["family"] == "Fira Code"
        assert d["size"] == 12.0

    def test_from_dict(self):
        font = FontConfig.from_dict({"family": "Fira Code", "size": 12.0})
        assert font.family == "Fira Code"
        assert font.size == 12.0

    def test_new_fields(self):
        """Test new FontConfig fields."""
        font = FontConfig(
            family="JetBrains Mono",
            size=14.0,
            cell_width=1.1,
            weight=FontWeight.BOLD,
            style=FontStyle.ITALIC,
            bold_italic_font="JetBrains Mono Bold Italic",
            anti_aliasing=True,
            fallback_fonts=["Menlo", "Monaco"],
        )
        assert font.cell_width == 1.1
        assert font.weight == FontWeight.BOLD
        assert font.style == FontStyle.ITALIC
        assert font.bold_italic_font == "JetBrains Mono Bold Italic"
        assert font.anti_aliasing is True
        assert font.fallback_fonts == ["Menlo", "Monaco"]

    def test_source_name_roundtrip(self):
        """Test storing and retrieving source names."""
        font = FontConfig(family="JetBrains Mono")
        font.set_source_name("iterm2", "JetBrainsMono-Regular")
        assert font.get_source_name("iterm2") == "JetBrainsMono-Regular"
        assert font.get_source_name("ghostty") is None

    def test_multiple_source_names(self):
        """Test storing source names from multiple terminals."""
        font = FontConfig(family="JetBrains Mono")
        font.set_source_name("iterm2", "JetBrainsMono-Regular")
        font.set_source_name("alacritty", "JetBrains Mono")
        assert font.get_source_name("iterm2") == "JetBrainsMono-Regular"
        assert font.get_source_name("alacritty") == "JetBrains Mono"

    def test_to_dict_with_new_fields(self):
        """Test serialization with new fields."""
        font = FontConfig(
            family="Fira Code",
            weight=FontWeight.BOLD,
            fallback_fonts=["Menlo"],
        )
        d = font.to_dict()
        assert d["family"] == "Fira Code"
        assert d["weight"] == "bold"
        assert d["fallback_fonts"] == ["Menlo"]

    def test_from_dict_with_new_fields(self):
        """Test deserialization with new fields."""
        font = FontConfig.from_dict(
            {
                "family": "Fira Code",
                "weight": "bold",
                "style": "italic",
                "fallback_fonts": ["Menlo", "Monaco"],
            }
        )
        assert font.family == "Fira Code"
        assert font.weight == FontWeight.BOLD
        assert font.style == FontStyle.ITALIC
        assert font.fallback_fonts == ["Menlo", "Monaco"]


class TestCursorConfig:
    """Tests for the CursorConfig class."""

    def test_cursor_style_enum(self):
        assert CursorStyle.BLOCK.value == "block"
        assert CursorStyle.BEAM.value == "beam"
        assert CursorStyle.UNDERLINE.value == "underline"

    def test_cursor_with_values(self):
        cursor = CursorConfig(style=CursorStyle.BEAM, blink=True, blink_interval=500)
        assert cursor.style == CursorStyle.BEAM
        assert cursor.blink is True
        assert cursor.blink_interval == 500

    def test_to_dict(self):
        cursor = CursorConfig(style=CursorStyle.BLOCK, blink=False)
        d = cursor.to_dict()
        assert d["style"] == "block"
        assert d["blink"] is False

    def test_from_dict(self):
        cursor = CursorConfig.from_dict({"style": "beam", "blink": True})
        assert cursor.style == CursorStyle.BEAM
        assert cursor.blink is True


class TestWindowConfig:
    """Tests for the WindowConfig class."""

    def test_window_with_values(self):
        window = WindowConfig(
            columns=120,
            rows=40,
            opacity=0.95,
            blur=20,
        )
        assert window.columns == 120
        assert window.rows == 40
        assert window.opacity == 0.95
        assert window.blur == 20

    def test_to_dict(self):
        window = WindowConfig(columns=80, rows=24)
        d = window.to_dict()
        assert d["columns"] == 80
        assert d["rows"] == 24

    def test_from_dict(self):
        window = WindowConfig.from_dict({"columns": 120, "opacity": 0.9})
        assert window.columns == 120
        assert window.opacity == 0.9


class TestBehaviorConfig:
    """Tests for the BehaviorConfig class."""

    def test_bell_mode_enum(self):
        assert BellMode.NONE.value == "none"
        assert BellMode.AUDIBLE.value == "audible"
        assert BellMode.VISUAL.value == "visual"

    def test_behavior_with_values(self):
        behavior = BehaviorConfig(
            shell="/bin/zsh",
            scrollback_lines=10000,
            bell_mode=BellMode.VISUAL,
        )
        assert behavior.shell == "/bin/zsh"
        assert behavior.scrollback_lines == 10000
        assert behavior.bell_mode == BellMode.VISUAL

    def test_to_dict(self):
        behavior = BehaviorConfig(shell="/bin/bash", bell_mode=BellMode.NONE)
        d = behavior.to_dict()
        assert d["shell"] == "/bin/bash"
        assert d["bell_mode"] == "none"

    def test_from_dict(self):
        behavior = BehaviorConfig.from_dict(
            {"shell": "/bin/zsh", "bell_mode": "audible"}
        )
        assert behavior.shell == "/bin/zsh"
        assert behavior.bell_mode == BellMode.AUDIBLE

    def test_environment_variables(self):
        """Test environment_variables field."""
        behavior = BehaviorConfig(
            shell="/bin/zsh",
            environment_variables={"EDITOR": "nvim", "COLORTERM": "truecolor"},
        )
        assert behavior.environment_variables == {
            "EDITOR": "nvim",
            "COLORTERM": "truecolor",
        }

    def test_shell_args(self):
        """Test shell_args field."""
        behavior = BehaviorConfig(
            shell="/bin/zsh",
            shell_args=["-l", "-i"],
        )
        assert behavior.shell_args == ["-l", "-i"]

    def test_to_dict_with_env_and_args(self):
        """Test to_dict includes environment_variables and shell_args."""
        behavior = BehaviorConfig(
            shell="/bin/zsh",
            shell_args=["-l"],
            environment_variables={"EDITOR": "vim"},
        )
        d = behavior.to_dict()
        assert d["shell"] == "/bin/zsh"
        assert d["shell_args"] == ["-l"]
        assert d["environment_variables"] == {"EDITOR": "vim"}

    def test_from_dict_with_env_and_args(self):
        """Test from_dict parses environment_variables and shell_args."""
        behavior = BehaviorConfig.from_dict(
            {
                "shell": "/bin/bash",
                "shell_args": ["-l", "-i"],
                "environment_variables": {"PATH": "/usr/bin", "HOME": "/home/user"},
            }
        )
        assert behavior.shell == "/bin/bash"
        assert behavior.shell_args == ["-l", "-i"]
        assert behavior.environment_variables == {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
        }


class TestKeyBinding:
    """Tests for the KeyBinding class."""

    def test_key_binding(self):
        kb = KeyBinding(action="copy", key="c", mods=["ctrl", "shift"])
        assert kb.action == "copy"
        assert kb.key == "c"
        assert kb.mods == ["ctrl", "shift"]

    def test_key_binding_no_mods(self):
        kb = KeyBinding(action="enter", key="Return")
        assert kb.mods == []

    def test_to_dict(self):
        kb = KeyBinding(action="paste", key="v", mods=["ctrl"])
        d = kb.to_dict()
        assert d["action"] == "paste"
        assert d["key"] == "v"
        assert d["mods"] == ["ctrl"]

    def test_from_dict(self):
        kb = KeyBinding.from_dict({"action": "copy", "key": "c", "mods": ["ctrl"]})
        assert kb.action == "copy"
        assert kb.key == "c"
        assert kb.mods == ["ctrl"]


class TestTerminalSpecificSetting:
    """Tests for the TerminalSpecificSetting class."""

    def test_terminal_specific(self):
        setting = TerminalSpecificSetting(
            terminal="iterm2",
            key="Unlimited Scrollback",
            value=True,
        )
        assert setting.terminal == "iterm2"
        assert setting.key == "Unlimited Scrollback"
        assert setting.value is True

    def test_to_dict(self):
        setting = TerminalSpecificSetting(
            terminal="kitty",
            key="allow_remote_control",
            value="yes",
        )
        d = setting.to_dict()
        assert d["terminal"] == "kitty"
        assert d["key"] == "allow_remote_control"
        assert d["value"] == "yes"

    def test_from_dict(self):
        setting = TerminalSpecificSetting.from_dict(
            {
                "terminal": "ghostty",
                "key": "gtk-single-instance",
                "value": True,
            }
        )
        assert setting.terminal == "ghostty"
        assert setting.key == "gtk-single-instance"
        assert setting.value is True


class TestCTEC:
    """Tests for the main CTEC class."""

    def test_empty_ctec(self):
        ctec = CTEC()
        assert ctec.version == "1.0"
        assert ctec.source_terminal is None
        assert ctec.color_scheme is None
        assert ctec.key_bindings == []
        assert ctec.terminal_specific == []
        assert ctec.warnings == []

    def test_ctec_with_config(self):
        ctec = CTEC(
            source_terminal="ghostty",
            font=FontConfig(family="JetBrains Mono"),
            cursor=CursorConfig(style=CursorStyle.BLOCK),
        )
        assert ctec.source_terminal == "ghostty"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.cursor.style == CursorStyle.BLOCK

    def test_add_warning(self):
        ctec = CTEC()
        ctec.add_warning("Test warning")
        assert "Test warning" in ctec.warnings

    def test_add_terminal_specific(self):
        ctec = CTEC()
        ctec.add_terminal_specific("iterm2", "test_key", "test_value")
        assert len(ctec.terminal_specific) == 1
        assert ctec.terminal_specific[0].terminal == "iterm2"

    def test_get_terminal_specific(self):
        ctec = CTEC()
        ctec.add_terminal_specific("iterm2", "key1", "value1")
        ctec.add_terminal_specific("ghostty", "key2", "value2")
        ctec.add_terminal_specific("iterm2", "key3", "value3")

        iterm_settings = ctec.get_terminal_specific("iterm2")
        assert len(iterm_settings) == 2

        ghostty_settings = ctec.get_terminal_specific("ghostty")
        assert len(ghostty_settings) == 1

    def test_to_dict(self):
        ctec = CTEC(
            source_terminal="kitty",
            font=FontConfig(family="Fira Code", size=12.0),
        )
        d = ctec.to_dict()
        assert d["version"] == "1.0"
        assert d["source_terminal"] == "kitty"
        assert d["font"]["family"] == "Fira Code"

    def test_from_dict(self):
        ctec = CTEC.from_dict(
            {
                "version": "1.0",
                "source_terminal": "alacritty",
                "font": {"family": "Monaco", "size": 14.0},
            }
        )
        assert ctec.source_terminal == "alacritty"
        assert ctec.font.family == "Monaco"
        assert ctec.font.size == 14.0

    def test_full_roundtrip(self):
        """Test that CTEC can be converted to dict and back."""
        original = CTEC(
            source_terminal="wezterm",
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            ),
            font=FontConfig(family="JetBrains Mono", size=14.0),
            cursor=CursorConfig(style=CursorStyle.BEAM, blink=True),
            window=WindowConfig(columns=120, rows=40, opacity=0.95),
            behavior=BehaviorConfig(shell="/bin/zsh", scrollback_lines=10000),
            key_bindings=[
                KeyBinding(action="copy", key="c", mods=["ctrl"]),
            ],
        )
        original.add_terminal_specific("wezterm", "test_key", "test_value")
        original.add_warning("Test warning")

        # Convert to dict and back
        d = original.to_dict()
        restored = CTEC.from_dict(d)

        # Verify all fields
        assert restored.source_terminal == "wezterm"
        assert restored.color_scheme.foreground.r == 255
        assert restored.font.family == "JetBrains Mono"
        assert restored.cursor.style == CursorStyle.BEAM
        assert restored.window.columns == 120
        assert restored.behavior.shell == "/bin/zsh"
        assert len(restored.key_bindings) == 1
        assert len(restored.terminal_specific) == 1


class TestScrollConfig:
    """Tests for the ScrollConfig class."""

    def test_default_config(self):
        """Test that default ScrollConfig has all None values."""
        config = ScrollConfig()
        assert config.unlimited is None
        assert config.disabled is None
        assert config.lines is None
        assert config.multiplier is None

    def test_from_lines_positive(self):
        """Test creating config from positive line count."""
        config = ScrollConfig.from_lines(10000)
        assert config.lines == 10000
        assert config.unlimited is None
        assert config.disabled is None

    def test_from_lines_unlimited(self):
        """Test that -1 lines means unlimited."""
        config = ScrollConfig.from_lines(-1)
        assert config.unlimited is True
        assert config.lines is None
        assert config.disabled is None

    def test_from_lines_disabled(self):
        """Test that 0 lines means disabled."""
        config = ScrollConfig.from_lines(0)
        assert config.disabled is True
        assert config.lines is None
        assert config.unlimited is None

    def test_from_bytes_positive(self):
        """Test creating config from byte count."""
        config = ScrollConfig.from_bytes(1000000)  # 1MB
        # 1MB / 100 bytes per line = 10000 lines
        assert config.lines == 10000
        assert config.unlimited is None
        assert config.disabled is None

    def test_from_bytes_disabled(self):
        """Test that 0 bytes means disabled."""
        config = ScrollConfig.from_bytes(0)
        assert config.disabled is True
        assert config.lines is None

    def test_from_bytes_custom_bytes_per_line(self):
        """Test from_bytes with custom bytes per line estimate."""
        config = ScrollConfig.from_bytes(5000, bytes_per_line=50)
        assert config.lines == 100  # 5000 / 50 = 100

    def test_get_effective_lines_explicit(self):
        """Test get_effective_lines with explicit line count."""
        config = ScrollConfig(lines=5000)
        assert config.get_effective_lines() == 5000

    def test_get_effective_lines_unlimited(self):
        """Test get_effective_lines with unlimited returns max."""
        config = ScrollConfig(unlimited=True)
        assert config.get_effective_lines(max_lines=100000) == 100000
        assert config.get_effective_lines(max_lines=50000) == 50000

    def test_get_effective_lines_disabled(self):
        """Test get_effective_lines with disabled returns 0."""
        config = ScrollConfig(disabled=True)
        assert config.get_effective_lines() == 0

    def test_get_effective_lines_default(self):
        """Test get_effective_lines returns default when nothing set."""
        config = ScrollConfig()
        assert config.get_effective_lines(default=10000) == 10000
        assert config.get_effective_lines(default=5000) == 5000

    def test_get_effective_lines_capped_at_max(self):
        """Test get_effective_lines caps at max_lines."""
        config = ScrollConfig(lines=200000)
        assert config.get_effective_lines(max_lines=100000) == 100000

    def test_get_effective_bytes_explicit_lines(self):
        """Test get_effective_bytes converts lines to bytes."""
        config = ScrollConfig(lines=10000)
        # 10000 lines * 100 bytes/line = 1000000 bytes
        assert config.get_effective_bytes() == 1000000

    def test_get_effective_bytes_unlimited(self):
        """Test get_effective_bytes with unlimited returns 100MB."""
        config = ScrollConfig(unlimited=True)
        assert config.get_effective_bytes() == 104857600  # 100MB

    def test_get_effective_bytes_disabled(self):
        """Test get_effective_bytes with disabled returns 0."""
        config = ScrollConfig(disabled=True)
        assert config.get_effective_bytes() == 0

    def test_get_effective_bytes_default(self):
        """Test get_effective_bytes returns default when nothing set."""
        config = ScrollConfig()
        assert config.get_effective_bytes(default_bytes=10485760) == 10485760

    def test_multiplier(self):
        """Test scroll multiplier/speed setting."""
        config = ScrollConfig(multiplier=3.0)
        assert config.multiplier == 3.0

    def test_combined_settings(self):
        """Test config with lines and multiplier."""
        config = ScrollConfig(lines=5000, multiplier=2.0)
        assert config.lines == 5000
        assert config.multiplier == 2.0
        assert config.get_effective_lines() == 5000

    def test_to_dict(self):
        """Test serialization to dict."""
        config = ScrollConfig(lines=10000, multiplier=3.0)
        d = config.to_dict()
        assert d["lines"] == 10000
        assert d["multiplier"] == 3.0
        # None values should not appear
        assert "unlimited" not in d or d["unlimited"] is None
        assert "disabled" not in d or d["disabled"] is None

    def test_from_dict(self):
        """Test deserialization from dict."""
        d = {"lines": 10000, "multiplier": 3.0}
        config = ScrollConfig.from_dict(d)
        assert config.lines == 10000
        assert config.multiplier == 3.0

    def test_from_dict_unlimited(self):
        """Test deserialization with unlimited flag."""
        d = {"unlimited": True}
        config = ScrollConfig.from_dict(d)
        assert config.unlimited is True

    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict round-trips correctly."""
        original = ScrollConfig(lines=8000, multiplier=2.5)
        restored = ScrollConfig.from_dict(original.to_dict())
        assert restored.lines == original.lines
        assert restored.multiplier == original.multiplier
