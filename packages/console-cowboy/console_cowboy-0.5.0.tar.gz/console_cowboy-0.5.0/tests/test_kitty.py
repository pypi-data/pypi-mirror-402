"""Tests for the Kitty adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BellMode,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
)
from console_cowboy.terminals import KittyAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestKittyAdapter:
    """Tests for the Kitty adapter."""

    def test_adapter_metadata(self):
        assert KittyAdapter.name == "kitty"
        assert ".conf" in KittyAdapter.config_extensions

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(config_path)

        assert ctec.source_terminal == "kitty"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # Check foreground (#c5c8c6)
        assert ctec.color_scheme.foreground.r == 197

    def test_parse_behavior(self):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(config_path)

        assert ctec.behavior is not None
        assert ctec.behavior.shell == "/bin/zsh"
        assert ctec.behavior.bell_mode == BellMode.VISUAL
        # Scrollback is now in ctec.scroll, not behavior
        assert ctec.scroll is not None
        assert ctec.scroll.lines == 10000

    def test_export(self):
        ctec = CTEC(
            font=FontConfig(family="Fira Code", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BEAM, blink=True),
        )
        output = KittyAdapter.export(ctec)

        assert "font_family Fira Code" in output
        assert "font_size 12.0" in output
        assert "cursor_shape beam" in output

    def test_key_bindings(self):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(config_path)

        assert len(ctec.key_bindings) > 0

    def test_terminal_specific_settings(self):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(config_path)

        kitty_specific = ctec.get_terminal_specific("kitty")
        assert len(kitty_specific) > 0


class TestKittyPowerUserSettings:
    """Tests for Kitty power user configuration support (Issue #44)."""

    def test_include_directive_warning(self):
        """Test that include directives generate warnings."""
        config = """
font_family JetBrains Mono
include themes/monokai.conf
globinclude themes/*.conf
envinclude KITTY_CONF_*
"""
        ctec = KittyAdapter.parse("test", content=config)

        # Should have 3 warnings for the include directives
        include_warnings = [w for w in ctec.warnings if "include" in w.lower()]
        assert len(include_warnings) == 3

        # Each warning should mention the specific directive
        assert any("themes/monokai.conf" in w for w in include_warnings)
        assert any("themes/*.conf" in w for w in include_warnings)
        assert any("KITTY_CONF_*" in w for w in include_warnings)

        # Include directives should still be stored in terminal_specific
        kitty_specific = ctec.get_terminal_specific("kitty")
        specific_keys = [s.key for s in kitty_specific]
        assert "include" in specific_keys
        assert "globinclude" in specific_keys
        assert "envinclude" in specific_keys

    def test_font_features_preserved(self):
        """Test that font_features are preserved in terminal_specific."""
        config = """
font_family JetBrains Mono
font_features JetBrainsMono-Regular +zero +ss01
font_features FiraCode-Regular +cv02 +ss03
"""
        ctec = KittyAdapter.parse("test", content=config)

        # Font features should be stored in terminal_specific
        kitty_specific = ctec.get_terminal_specific("kitty")
        font_feature_settings = [s for s in kitty_specific if s.key == "font_features"]

        # Both font_features lines should be preserved
        assert len(font_feature_settings) == 2
        values = [s.value for s in font_feature_settings]
        assert any("+zero" in v and "+ss01" in v for v in values)
        assert any("+cv02" in v and "+ss03" in v for v in values)

    def test_font_features_roundtrip(self):
        """Test that font_features round-trip correctly."""
        config = """
font_features JetBrainsMono-Regular +zero +ss01
font_features FiraCode-Regular +cv02 +ss03
"""
        ctec = KittyAdapter.parse("test", content=config)
        output = KittyAdapter.export(ctec)

        # Both font_features lines should appear in output
        assert "font_features JetBrainsMono-Regular +zero +ss01" in output
        assert "font_features FiraCode-Regular +cv02 +ss03" in output

    def test_mouse_map_preserved(self):
        """Test that mouse_map bindings are preserved in terminal_specific."""
        config = """
mouse_map left click ungrabbed mouse_handle_click selection link prompt
mouse_map ctrl+left click ungrabbed mouse_handle_click selection link
mouse_map right press ungrabbed paste_from_selection
"""
        ctec = KittyAdapter.parse("test", content=config)

        # Mouse mappings should be stored in terminal_specific
        kitty_specific = ctec.get_terminal_specific("kitty")
        mouse_map_settings = [s for s in kitty_specific if s.key == "mouse_map"]

        # All 3 mouse_map lines should be preserved
        assert len(mouse_map_settings) == 3

    def test_mouse_map_roundtrip(self):
        """Test that mouse_map round-trips correctly."""
        config = """
mouse_map left click ungrabbed mouse_handle_click selection link prompt
mouse_map ctrl+left click ungrabbed mouse_handle_click selection link
"""
        ctec = KittyAdapter.parse("test", content=config)
        output = KittyAdapter.export(ctec)

        # Both mouse_map lines should appear in output
        assert (
            "mouse_map left click ungrabbed mouse_handle_click selection link prompt"
            in output
        )
        assert (
            "mouse_map ctrl+left click ungrabbed mouse_handle_click selection link"
            in output
        )

    def test_url_color_maps_to_link(self):
        """Test that url_color maps to color_scheme.link."""
        config = """
url_color #0087ff
foreground #c5c8c6
background #1d1f21
"""
        ctec = KittyAdapter.parse("test", content=config)

        # url_color should be mapped to color_scheme.link
        assert ctec.color_scheme is not None
        assert ctec.color_scheme.link is not None
        assert ctec.color_scheme.link.to_hex() == "#0087ff"

    def test_url_color_export(self):
        """Test that color_scheme.link exports as url_color."""
        ctec = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(197, 200, 198),
                background=Color(29, 31, 33),
                link=Color(0, 135, 255),  # Blue URL color
            )
        )
        output = KittyAdapter.export(ctec)

        # link should be exported as url_color
        assert "url_color #0087ff" in output

    def test_extended_colors_preserved(self):
        """Test that extended colors (color16-255) are preserved."""
        config = """
color16 #000000
color17 #00005f
color255 #eeeeee
"""
        ctec = KittyAdapter.parse("test", content=config)

        # Extended colors should be stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "color16") == "#000000"
        assert ctec.get_terminal_specific("kitty", "color17") == "#00005f"
        assert ctec.get_terminal_specific("kitty", "color255") == "#eeeeee"

    def test_extended_colors_roundtrip(self):
        """Test that extended colors round-trip correctly."""
        config = """
color16 #000000
color255 #eeeeee
"""
        ctec = KittyAdapter.parse("test", content=config)
        output = KittyAdapter.export(ctec)

        # Extended colors should appear in output
        assert "color16 #000000" in output
        assert "color255 #eeeeee" in output

    def test_shell_integration_preserved(self):
        """Test that shell_integration is preserved in terminal_specific."""
        config = """
shell_integration enabled
"""
        ctec = KittyAdapter.parse("test", content=config)

        # shell_integration should be stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "shell_integration") == "enabled"

    def test_startup_session_preserved(self):
        """Test that startup_session is preserved in terminal_specific."""
        config = """
startup_session ~/.config/kitty/startup.conf
"""
        ctec = KittyAdapter.parse("test", content=config)

        # startup_session should be stored in terminal_specific
        assert (
            ctec.get_terminal_specific("kitty", "startup_session")
            == "~/.config/kitty/startup.conf"
        )

    def test_scrollback_pager_preserved(self):
        """Test that scrollback_pager settings are preserved."""
        config = """
scrollback_pager nvim -c 'set ft=man' -
scrollback_pager_history_size 10000
"""
        ctec = KittyAdapter.parse("test", content=config)

        # Both settings should be preserved
        assert (
            ctec.get_terminal_specific("kitty", "scrollback_pager")
            == "nvim -c 'set ft=man' -"
        )
        assert (
            ctec.get_terminal_specific("kitty", "scrollback_pager_history_size")
            == "10000"
        )

    def test_macos_options_preserved(self):
        """Test that macOS-specific options are preserved."""
        config = """
macos_option_as_alt yes
macos_titlebar_color background
macos_quit_when_last_window_closed yes
"""
        ctec = KittyAdapter.parse("test", content=config)

        # macOS options should be stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "macos_option_as_alt") == "yes"
        assert (
            ctec.get_terminal_specific("kitty", "macos_titlebar_color") == "background"
        )
        assert (
            ctec.get_terminal_specific("kitty", "macos_quit_when_last_window_closed")
            == "yes"
        )

    def test_power_user_config_roundtrip(self):
        """Test complete power user config round-trips correctly."""
        config = """
# Power user configuration
shell_integration enabled
startup_session ~/.config/kitty/startup.conf
scrollback_pager nvim -c 'set ft=man' -
font_features JetBrainsMono-Regular +zero +ss01
mouse_map left click ungrabbed mouse_handle_click selection link prompt
macos_option_as_alt yes
url_color #0087ff
"""
        ctec = KittyAdapter.parse("test", content=config)
        output = KittyAdapter.export(ctec)

        # All settings should round-trip
        assert "shell_integration enabled" in output
        assert "startup_session ~/.config/kitty/startup.conf" in output
        assert "scrollback_pager nvim -c 'set ft=man' -" in output
        assert "font_features JetBrainsMono-Regular +zero +ss01" in output
        assert (
            "mouse_map left click ungrabbed mouse_handle_click selection link prompt"
            in output
        )
        assert "macos_option_as_alt yes" in output
        assert "url_color #0087ff" in output
