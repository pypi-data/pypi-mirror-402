"""Tests for font-related bug fixes."""

import pytest

from console_cowboy.ctec.schema import (
    CTEC,
    FontConfig,
    FontStyle,
    FontWeight,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    ITerm2Adapter,
    KittyAdapter,
    WeztermAdapter,
)


class TestKittyLigaturesFix:
    """Test that Kitty ligatures round-trip correctly (Bug fix #1)."""

    def test_ligatures_enabled_roundtrip(self):
        """Test ligatures=True exports as disable_ligatures=never and imports back correctly."""
        ctec = CTEC(font=FontConfig(family="JetBrains Mono", ligatures=True))
        exported = KittyAdapter.export(ctec)

        # Should export as "never" (meaning ligatures are NOT disabled)
        assert "disable_ligatures never" in exported

        # Import back
        imported = KittyAdapter.parse("test", content=exported)
        assert imported.font.ligatures is True

    def test_ligatures_disabled_roundtrip(self):
        """Test ligatures=False exports as disable_ligatures=always and imports back correctly."""
        ctec = CTEC(font=FontConfig(family="JetBrains Mono", ligatures=False))
        exported = KittyAdapter.export(ctec)

        # Should export as "always" (meaning ligatures ARE disabled)
        assert "disable_ligatures always" in exported

        # Import back
        imported = KittyAdapter.parse("test", content=exported)
        assert imported.font.ligatures is False

    def test_parse_disable_ligatures_never(self):
        """Test parsing disable_ligatures = never correctly sets ligatures=True."""
        content = """
font_family JetBrains Mono
disable_ligatures never
"""
        ctec = KittyAdapter.parse("test", content=content)
        assert ctec.font.ligatures is True

    def test_parse_disable_ligatures_always(self):
        """Test parsing disable_ligatures = always correctly sets ligatures=False."""
        content = """
font_family JetBrains Mono
disable_ligatures always
"""
        ctec = KittyAdapter.parse("test", content=content)
        assert ctec.font.ligatures is False


class TestGhosttyCellWidthFix:
    """Test that Ghostty adjust-cell-width handles percentages (Bug fix #2)."""

    def test_parse_cell_width_integer(self):
        """Test parsing integer value like adjust-cell-width = 5."""
        content = """
font-family = JetBrains Mono
adjust-cell-width = 5
"""
        ctec = GhosttyAdapter.parse("test", content=content)
        # 5% increase = 1.05
        assert ctec.font.cell_width == pytest.approx(1.05)

    def test_parse_cell_width_percentage(self):
        """Test parsing percentage value like adjust-cell-width = 5%."""
        content = """
font-family = JetBrains Mono
adjust-cell-width = 5%
"""
        ctec = GhosttyAdapter.parse("test", content=content)
        # 5% increase = 1.05
        assert ctec.font.cell_width == pytest.approx(1.05)

    def test_cell_width_roundtrip(self):
        """Test cell_width exports and imports correctly."""
        ctec = CTEC(font=FontConfig(family="JetBrains Mono", cell_width=1.10))
        exported = GhosttyAdapter.export(ctec)

        # Should export as integer (10 for 10%)
        assert "adjust-cell-width = 10" in exported

        # Import back
        imported = GhosttyAdapter.parse("test", content=exported)
        assert imported.font.cell_width == pytest.approx(1.10)


class TestWeztermWeightWithFallbacks:
    """Test that WezTerm preserves weight when fallbacks are present (Bug fix #4)."""

    def test_export_weight_with_fallbacks(self):
        """Test that weight is exported when both weight and fallbacks are set."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                weight=FontWeight.BOLD,
                fallback_fonts=["Symbols Nerd Font"],
            )
        )
        exported = WeztermAdapter.export(ctec)

        # Should include both weight and fallbacks in font_with_fallback
        assert 'family = "JetBrains Mono"' in exported
        assert 'weight = "Bold"' in exported
        assert "Symbols Nerd Font" in exported
        assert "font_with_fallback" in exported

    def test_parse_weight_with_fallbacks(self):
        """Test parsing wezterm.font_with_fallback with weight."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.font = wezterm.font_with_fallback({ { family = "JetBrains Mono", weight = "Bold" }, "Symbols Nerd Font" })

return config
"""
        ctec = WeztermAdapter.parse("test", content=content)
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.weight == FontWeight.BOLD
        assert ctec.font.fallback_fonts == ["Symbols Nerd Font"]

    def test_weight_only_export(self):
        """Test weight without fallbacks exports as wezterm.font with weight parameter."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                weight=FontWeight.BOLD,
            )
        )
        exported = WeztermAdapter.export(ctec)

        # Should use simple font with weight parameter
        assert 'wezterm.font("JetBrains Mono"' in exported
        assert 'weight = "Bold"' in exported


class TestAlacrittyFontStyle:
    """Test that Alacritty parses font style attribute (Bug fix #5)."""

    def test_parse_italic_style(self):
        """Test parsing font.normal.style = Italic."""
        content = """
[font]
size = 12

[font.normal]
family = "JetBrains Mono"
style = "Italic"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.style == FontStyle.ITALIC

    def test_parse_oblique_style(self):
        """Test parsing font.normal.style = Oblique."""
        content = """
[font]
size = 12

[font.normal]
family = "JetBrains Mono"
style = "Oblique"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)
        assert ctec.font.style == FontStyle.OBLIQUE

    def test_export_font_style(self):
        """Test that font style is exported correctly."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                style=FontStyle.ITALIC,
            )
        )
        exported = AlacrittyAdapter.export(ctec)

        # Should include style in the output
        assert '"Italic"' in exported or "'Italic'" in exported


class TestKittySymbolMap:
    """Test Kitty symbol_map support."""

    def test_parse_symbol_map(self):
        """Test parsing symbol_map directive."""
        content = """
font_family JetBrains Mono
symbol_map U+E0A0-U+E0A3,U+E0B0-U+E0B3 Symbols Nerd Font
symbol_map U+F000-U+F8FF Font Awesome
"""
        ctec = KittyAdapter.parse("test", content=content)
        assert ctec.font.symbol_map is not None
        assert len(ctec.font.symbol_map) == 2
        assert (
            ctec.font.symbol_map["U+E0A0-U+E0A3,U+E0B0-U+E0B3"] == "Symbols Nerd Font"
        )
        assert ctec.font.symbol_map["U+F000-U+F8FF"] == "Font Awesome"

    def test_export_symbol_map(self):
        """Test exporting symbol_map."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                symbol_map={
                    "U+E0A0-U+E0A3": "Powerline Symbols",
                    "U+F000-U+F8FF": "Font Awesome",
                },
            )
        )
        exported = KittyAdapter.export(ctec)

        assert "symbol_map U+E0A0-U+E0A3 Powerline Symbols" in exported
        assert "symbol_map U+F000-U+F8FF Font Awesome" in exported

    def test_symbol_map_roundtrip(self):
        """Test symbol_map round-trips correctly."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                symbol_map={"U+E0A0-U+E0B3": "Nerd Symbols"},
            )
        )
        exported = KittyAdapter.export(ctec)
        imported = KittyAdapter.parse("test", content=exported)

        assert imported.font.symbol_map is not None
        assert imported.font.symbol_map["U+E0A0-U+E0B3"] == "Nerd Symbols"


class TestITerm2PowerlineGlyphs:
    """Test iTerm2 Powerline glyphs support."""

    def test_export_powerline_glyphs(self):
        """Test exporting draw_powerline_glyphs."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                draw_powerline_glyphs=True,
            )
        )
        exported = ITerm2Adapter.export(ctec)

        # Parse the plist output
        import plistlib

        data = plistlib.loads(exported.encode())
        profile = data["New Bookmarks"][0]
        assert profile["Draw Powerline Glyphs"] is True


class TestFontConfigNewFields:
    """Test new FontConfig fields round-trip correctly."""

    def test_symbol_map_serialization(self):
        """Test symbol_map serializes and deserializes correctly."""
        font = FontConfig(
            family="Test",
            symbol_map={"U+E000-U+F000": "Symbols"},
        )
        data = font.to_dict()
        assert "symbol_map" in data
        assert data["symbol_map"]["U+E000-U+F000"] == "Symbols"

        restored = FontConfig.from_dict(data)
        assert restored.symbol_map == font.symbol_map

    def test_draw_powerline_glyphs_serialization(self):
        """Test draw_powerline_glyphs serializes correctly."""
        font = FontConfig(
            family="Test",
            draw_powerline_glyphs=True,
        )
        data = font.to_dict()
        assert data["draw_powerline_glyphs"] is True

        restored = FontConfig.from_dict(data)
        assert restored.draw_powerline_glyphs is True

    def test_box_drawing_scale_serialization(self):
        """Test box_drawing_scale serializes correctly."""
        font = FontConfig(
            family="Test",
            box_drawing_scale=0.8,
        )
        data = font.to_dict()
        assert data["box_drawing_scale"] == 0.8

        restored = FontConfig.from_dict(data)
        assert restored.box_drawing_scale == 0.8
