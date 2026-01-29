"""Tests for the macOS Terminal.app adapter."""

from pathlib import Path
from unittest.mock import patch

import pytest

from console_cowboy.ctec.schema import (
    CTEC,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    WindowConfig,
)
from console_cowboy.terminals import GhosttyAdapter, TerminalAppAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTerminalAppAdapter:
    """Tests for the macOS Terminal.app adapter."""

    def test_adapter_metadata(self):
        assert TerminalAppAdapter.name == "terminal_app"
        assert TerminalAppAdapter.display_name == "Terminal.app"
        assert ".terminal" in TerminalAppAdapter.config_extensions
        assert ".plist" in TerminalAppAdapter.config_extensions
        assert (
            "Library/Preferences/com.apple.Terminal.plist"
            in TerminalAppAdapter.default_config_paths
        )

    def test_parse_terminal_file(self):
        """Test parsing exported .terminal file."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.source_terminal == "terminal_app"
        assert ctec.color_scheme is not None
        assert ctec.font is not None
        assert ctec.cursor is not None
        assert ctec.window is not None

    def test_parse_colors(self):
        """Test color parsing from .terminal file."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # Foreground should be #c5c8c6 (197, 200, 198)
        assert ctec.color_scheme.foreground is not None
        assert ctec.color_scheme.foreground.r == 197
        assert ctec.color_scheme.foreground.g == 200
        assert ctec.color_scheme.foreground.b == 198
        # Background should be #1d1f21 (29, 31, 33)
        assert ctec.color_scheme.background is not None
        assert ctec.color_scheme.background.r == 29
        assert ctec.color_scheme.background.g == 31
        assert ctec.color_scheme.background.b == 33

    def test_parse_font(self):
        """Test font parsing from .terminal file."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.font is not None
        assert ctec.font.family == "Monaco"
        assert ctec.font.size == 14.0
        assert ctec.font.anti_aliasing is True

    def test_parse_cursor(self):
        """Test cursor settings parsing."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.cursor is not None
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.cursor.blink is True

    def test_parse_window(self):
        """Test window settings parsing."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.window is not None
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40
        assert ctec.window.opacity == 0.95

    def test_parse_scroll(self):
        """Test scroll settings parsing."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        assert ctec.scroll is not None
        assert ctec.scroll.lines == 10000

    def test_parse_multi_profile_plist(self):
        """Test parsing full com.apple.Terminal.plist with multiple profiles."""
        config_path = FIXTURES_DIR / "terminal_app" / "com.apple.Terminal.plist"
        ctec = TerminalAppAdapter.parse(config_path)

        # Should use default profile "Pro"
        assert ctec.source_terminal == "terminal_app"
        # Pro profile has white text on black background
        assert ctec.color_scheme.foreground.r == 255
        assert ctec.color_scheme.background.r == 0
        # Should have warning about multiple profiles
        assert any("profiles" in w.lower() for w in ctec.warnings)

    def test_parse_specific_profile(self):
        """Test parsing a specific profile from multi-profile plist."""
        config_path = FIXTURES_DIR / "terminal_app" / "com.apple.Terminal.plist"
        ctec = TerminalAppAdapter.parse(config_path, profile_name="Custom")

        # Custom profile has beam cursor
        assert ctec.cursor.style == CursorStyle.BEAM
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40

    def test_parse_invalid_profile_raises(self):
        """Test that requesting non-existent profile raises ValueError."""
        config_path = FIXTURES_DIR / "terminal_app" / "com.apple.Terminal.plist"
        with pytest.raises(ValueError, match="Profile 'NonExistent' not found"):
            TerminalAppAdapter.parse(config_path, profile_name="NonExistent")

    def test_export(self):
        """Test exporting CTEC to .terminal format."""
        ctec = CTEC(
            font=FontConfig(family="Menlo", size=12.0, anti_aliasing=True),
            cursor=CursorConfig(style=CursorStyle.UNDERLINE, blink=False),
            window=WindowConfig(columns=100, rows=30, opacity=0.9),
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            ),
        )
        output = TerminalAppAdapter.export(ctec)

        # Should be valid plist XML
        assert '<?xml version="1.0"' in output
        assert "<plist" in output
        assert "Window Settings" in output

    def test_export_produces_valid_plist(self):
        """Test that export produces valid plist."""
        import plistlib

        ctec = CTEC(
            font=FontConfig(family="Monaco", size=14.0),
            cursor=CursorConfig(style=CursorStyle.BLOCK),
        )
        output = TerminalAppAdapter.export(ctec)
        # Should not raise
        data = plistlib.loads(output.encode())
        assert isinstance(data, dict)

    def test_roundtrip(self):
        """Test parse -> export -> parse preserves settings."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        original = TerminalAppAdapter.parse(config_path)

        exported = TerminalAppAdapter.export(original)
        restored = TerminalAppAdapter.parse("test.terminal", content=exported)

        # Core settings should be preserved
        assert restored.color_scheme.foreground == original.color_scheme.foreground
        assert restored.color_scheme.background == original.color_scheme.background
        assert restored.cursor.style == original.cursor.style
        assert restored.cursor.blink == original.cursor.blink
        assert restored.window.columns == original.window.columns
        assert restored.window.rows == original.window.rows

    def test_terminal_specific_settings(self):
        """Test that terminal-specific settings are preserved."""
        config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
        ctec = TerminalAppAdapter.parse(config_path)

        terminal_specific = ctec.get_terminal_specific("terminal_app")
        # ProfileCurrentVersion should be stored
        version_setting = next(
            (s for s in terminal_specific if s.key == "ProfileCurrentVersion"),
            None,
        )
        assert version_setting is not None
        assert version_setting.value == 2.07

    def test_terminal_app_to_ghostty(self):
        """Test converting from Terminal.app to Ghostty."""
        # Mock system font lookup to ensure deterministic behavior across platforms
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            config_path = FIXTURES_DIR / "terminal_app" / "Basic.terminal"
            ctec = TerminalAppAdapter.parse(config_path)

            ghostty_output = GhosttyAdapter.export(ctec)
            ghostty_ctec = GhosttyAdapter.parse("test", content=ghostty_output)

            # Core settings should convert
            assert ghostty_ctec.font.family == ctec.font.family
            assert ghostty_ctec.font.size == ctec.font.size
            assert ghostty_ctec.cursor.style == ctec.cursor.style

    def test_ghostty_to_terminal_app(self):
        """Test converting from Ghostty to Terminal.app."""
        # Mock system font lookup to ensure deterministic behavior across platforms
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            ghostty_path = FIXTURES_DIR / "ghostty" / "config"
            ctec = GhosttyAdapter.parse(ghostty_path)

            terminal_output = TerminalAppAdapter.export(ctec)
            terminal_ctec = TerminalAppAdapter.parse(
                "test.terminal", content=terminal_output
            )

            # Core settings should convert
            assert terminal_ctec.font.family == ctec.font.family
            assert terminal_ctec.font.size == ctec.font.size
            assert terminal_ctec.cursor.style == ctec.cursor.style
