"""Tests for the Ghostty adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BackgroundImagePosition,
    BackgroundImageScale,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    WindowConfig,
)
from console_cowboy.terminals import GhosttyAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGhosttyAdapter:
    """Tests for the Ghostty adapter."""

    def test_adapter_metadata(self):
        assert GhosttyAdapter.name == "ghostty"
        assert GhosttyAdapter.display_name == "Ghostty"
        assert ".config/ghostty/config" in GhosttyAdapter.default_config_paths

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(config_path)

        assert ctec.source_terminal == "ghostty"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.cursor.blink is True
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40
        assert ctec.window.opacity == 0.95

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # Check foreground (#c5c8c6)
        assert ctec.color_scheme.foreground.r == 197
        assert ctec.color_scheme.foreground.g == 200
        assert ctec.color_scheme.foreground.b == 198
        # Check background (#1d1f21)
        assert ctec.color_scheme.background.r == 29

    def test_parse_from_content(self):
        content = """
font-family = Test Font
font-size = 16
cursor-style = bar
"""
        ctec = GhosttyAdapter.parse("test", content=content)
        assert ctec.font.family == "Test Font"
        assert ctec.font.size == 16.0
        assert ctec.cursor.style == CursorStyle.BEAM

    def test_export(self):
        ctec = CTEC(
            font=FontConfig(family="Fira Code", size=12.0),
            cursor=CursorConfig(style=CursorStyle.UNDERLINE, blink=False),
        )
        output = GhosttyAdapter.export(ctec)

        assert "font-family = Fira Code" in output
        assert "font-size = 12.0" in output
        assert "cursor-style = underline" in output
        assert "cursor-style-blink = false" in output

    def test_export_colors(self):
        ctec = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
                red=Color(204, 0, 0),
            )
        )
        output = GhosttyAdapter.export(ctec)

        assert "foreground = #ffffff" in output
        assert "background = #000000" in output
        assert "palette = 1=#cc0000" in output

    def test_roundtrip(self):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        original = GhosttyAdapter.parse(config_path)

        # Export and re-parse
        exported = GhosttyAdapter.export(original)
        restored = GhosttyAdapter.parse("test", content=exported)

        assert restored.font.family == original.font.family
        assert restored.font.size == original.font.size
        assert restored.cursor.style == original.cursor.style

    def test_parse_background_image(self):
        """Test parsing background image settings from Ghostty config."""
        content = """
background-image = /path/to/image.png
background-image-opacity = 0.5
"""
        ctec = GhosttyAdapter.parse("test", content=content)
        assert ctec.window.background_image == "/path/to/image.png"
        assert ctec.window.background_image_opacity == 0.5

    def test_parse_background_image_scale(self):
        """Test parsing background image fit/scale modes."""
        for ghostty_value, expected_scale in [
            ("contain", BackgroundImageScale.CONTAIN),
            ("cover", BackgroundImageScale.COVER),
            ("stretch", BackgroundImageScale.STRETCH),
            ("none", BackgroundImageScale.NONE),
        ]:
            content = f"""
background-image = /path/to/image.png
background-image-fit = {ghostty_value}
"""
            ctec = GhosttyAdapter.parse("test", content=content)
            assert ctec.window.background_image_scale == expected_scale

    def test_parse_background_image_position(self):
        """Test parsing background image position settings."""
        for position in [
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "center-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ]:
            content = f"""
background-image = /path/to/image.png
background-image-position = {position}
"""
            ctec = GhosttyAdapter.parse("test", content=content)
            assert ctec.window.background_image_position is not None
            assert ctec.window.background_image_position.value == position

    def test_parse_background_image_repeat(self):
        """Test that background-image-repeat=true sets scale to TILE."""
        content = """
background-image = /path/to/image.png
background-image-repeat = true
"""
        ctec = GhosttyAdapter.parse("test", content=content)
        assert ctec.window.background_image_scale == BackgroundImageScale.TILE

    def test_export_background_image(self):
        """Test exporting background image settings to Ghostty config."""
        ctec = CTEC(
            window=WindowConfig(
                background_image="/home/user/wallpaper.png",
                background_image_opacity=0.8,
            )
        )
        output = GhosttyAdapter.export(ctec)

        assert "background-image = /home/user/wallpaper.png" in output
        assert "background-image-opacity = 0.8" in output

    def test_export_background_image_scale_and_position(self):
        """Test exporting background image scale and position settings."""
        ctec = CTEC(
            window=WindowConfig(
                background_image="/path/to/image.png",
                background_image_scale=BackgroundImageScale.COVER,
                background_image_position=BackgroundImagePosition.CENTER,
            )
        )
        output = GhosttyAdapter.export(ctec)

        assert "background-image = /path/to/image.png" in output
        assert "background-image-fit = cover" in output
        assert "background-image-position = center" in output

    def test_roundtrip_background_image(self):
        """Test round-trip conversion of background image settings."""
        content = """
background-image = /path/to/wallpaper.png
background-image-opacity = 0.75
background-image-fit = contain
background-image-position = bottom-right
"""
        original = GhosttyAdapter.parse("test", content=content)
        exported = GhosttyAdapter.export(original)
        restored = GhosttyAdapter.parse("test", content=exported)

        assert restored.window.background_image == original.window.background_image
        assert (
            restored.window.background_image_opacity
            == original.window.background_image_opacity
        )
        assert (
            restored.window.background_image_scale
            == original.window.background_image_scale
        )
        assert (
            restored.window.background_image_position
            == original.window.background_image_position
        )

    def test_export_background_image_tile(self):
        """Test that BackgroundImageScale.TILE exports as background-image-repeat."""
        ctec = CTEC(
            window=WindowConfig(
                background_image="/path/to/image.png",
                background_image_scale=BackgroundImageScale.TILE,
            )
        )
        output = GhosttyAdapter.export(ctec)

        assert "background-image-repeat = true" in output
        assert "background-image-fit" not in output

    def test_export_background_image_centered_fallback(self):
        """Test that CENTERED scale mode falls back with warning for Ghostty."""
        ctec = CTEC(
            window=WindowConfig(
                background_image="/path/to/image.png",
                background_image_scale=BackgroundImageScale.CENTERED,
            )
        )
        output = GhosttyAdapter.export(ctec)

        # Should fall back to contain
        assert "background-image-fit = contain" in output
        # Should add a warning
        assert len(ctec.warnings) == 1
        assert "centered" in ctec.warnings[0].lower()


class TestGhosttyQuickTerminalFeatures:
    """Tests for Ghostty 1.2.0 quick terminal features (Issue #41)."""

    def test_ghostty_parse_quick_terminal_center_position(self):
        """Test Ghostty parses center position for quick terminal."""
        config = """
quick-terminal-position = center
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.enabled is True
        from console_cowboy.ctec.schema import QuickTerminalPosition

        assert ctec.quick_terminal.position == QuickTerminalPosition.CENTER

    def test_ghostty_export_quick_terminal_center_position(self):
        """Test Ghostty exports center position for quick terminal."""
        from console_cowboy.ctec.schema import (
            QuickTerminalConfig,
            QuickTerminalPosition,
        )

        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                position=QuickTerminalPosition.CENTER,
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "quick-terminal-position = center" in output

    def test_ghostty_parse_quick_terminal_size(self):
        """Test Ghostty parses quick-terminal-size."""
        # Test percentage
        config = """
quick-terminal-size = 50%
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.size == "50%"

        # Test pixels
        config = """
quick-terminal-size = 300px
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal.size == "300px"

        # Test combined width,height
        config = """
quick-terminal-size = 50%,500px
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal.size == "50%,500px"

    def test_ghostty_export_quick_terminal_size(self):
        """Test Ghostty exports quick-terminal-size."""
        from console_cowboy.ctec.schema import QuickTerminalConfig

        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                size="75%",
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "quick-terminal-size = 75%" in output

    def test_ghostty_parse_quick_terminal_autohide(self):
        """Test Ghostty parses quick-terminal-autohide."""
        config = """
quick-terminal-autohide = true
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.hide_on_focus_loss is True

        config = """
quick-terminal-autohide = false
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.quick_terminal.hide_on_focus_loss is False

    def test_ghostty_export_quick_terminal_autohide(self):
        """Test Ghostty exports quick-terminal-autohide."""
        from console_cowboy.ctec.schema import QuickTerminalConfig

        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                hide_on_focus_loss=True,
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "quick-terminal-autohide = true" in output


class TestGhosttyFontFeatures:
    """Tests for Ghostty font-feature support (Issue #41)."""

    def test_ghostty_parse_font_feature(self):
        """Test Ghostty parses font-feature settings."""
        config = """
font-feature = -calt
font-feature = ss01
font-feature = -liga
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.font is not None
        assert ctec.font.font_features is not None
        assert "-calt" in ctec.font.font_features
        assert "ss01" in ctec.font.font_features
        assert "-liga" in ctec.font.font_features

    def test_ghostty_export_font_features(self):
        """Test Ghostty exports font-feature settings."""
        from console_cowboy.ctec.schema import FontConfig

        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                font_features=["-calt", "ss01"],
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "font-feature = -calt" in output
        assert "font-feature = ss01" in output

    def test_ghostty_font_feature_roundtrip(self):
        """Test font-feature survives Ghostty round-trip."""
        original_config = """
font-family = JetBrains Mono
font-feature = -calt
font-feature = ss01
"""
        parsed = GhosttyAdapter.parse("test", content=original_config)
        exported = GhosttyAdapter.export(parsed)
        reparsed = GhosttyAdapter.parse("test", content=exported)

        assert "-calt" in reparsed.font.font_features
        assert "ss01" in reparsed.font.font_features


class TestGhosttyAdjustCellWidth:
    """Tests for Ghostty adjust-cell-width pixel vs percentage handling (Issue #41)."""

    def test_ghostty_parse_adjust_cell_width_percentage(self):
        """Test Ghostty parses adjust-cell-width with percentage."""
        config = """
adjust-cell-width = 5%
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.font is not None
        assert ctec.font.cell_width == 1.05  # 5% increase

    def test_ghostty_parse_adjust_cell_width_pixel(self):
        """Test Ghostty parses adjust-cell-width with pixel value."""
        config = """
adjust-cell-width = 2
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        # Pixel values are stored as terminal-specific since we can't convert
        assert ctec.get_terminal_specific("ghostty", "adjust-cell-width") == 2
        # Should have a warning about conversion
        assert any("pixel" in w.lower() for w in ctec.warnings)

    def test_ghostty_export_adjust_cell_width_with_percentage(self):
        """Test Ghostty exports adjust-cell-width with percentage suffix."""
        from console_cowboy.ctec.schema import FontConfig

        ctec = CTEC(
            font=FontConfig(
                family="Test",
                cell_width=1.1,  # 10% wider
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "adjust-cell-width = 10%" in output


class TestGhosttyWindowDecoration:
    """Tests for Ghostty window-decoration export fix (Issue #41)."""

    def test_ghostty_export_window_decoration_enabled(self):
        """Test Ghostty exports 'auto' instead of 'true' for decorations."""

        ctec = CTEC(window=WindowConfig(decorations=True))
        output = GhosttyAdapter.export(ctec)
        # Should use 'auto' not 'true' for cross-platform compatibility
        assert "window-decoration = auto" in output
        assert "window-decoration = true" not in output

    def test_ghostty_export_window_decoration_disabled(self):
        """Test Ghostty exports 'none' for disabled decorations."""

        ctec = CTEC(window=WindowConfig(decorations=False))
        output = GhosttyAdapter.export(ctec)
        assert "window-decoration = none" in output
