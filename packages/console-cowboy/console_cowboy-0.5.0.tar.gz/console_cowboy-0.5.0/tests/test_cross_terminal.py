"""Tests for converting between different terminals."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    Color,
    ColorScheme,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    KittyAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCrossTerminalConversion:
    """Tests for converting between different terminals."""

    def test_ghostty_to_alacritty(self):
        # Parse Ghostty config
        ghostty_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(ghostty_path)

        # Export to Alacritty
        alacritty_output = AlacrittyAdapter.export(ctec)

        # Re-parse as Alacritty
        alacritty_ctec = AlacrittyAdapter.parse("test.toml", content=alacritty_output)

        # Core settings should be preserved
        assert alacritty_ctec.font.family == ctec.font.family
        assert alacritty_ctec.font.size == ctec.font.size

    def test_kitty_to_ghostty(self):
        # Parse Kitty config
        kitty_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        ctec = KittyAdapter.parse(kitty_path)

        # Export to Ghostty
        ghostty_output = GhosttyAdapter.export(ctec)

        # Re-parse as Ghostty
        ghostty_ctec = GhosttyAdapter.parse("test", content=ghostty_output)

        # Core settings should be preserved
        assert ghostty_ctec.font.family == ctec.font.family
        assert ghostty_ctec.font.size == ctec.font.size

    def test_alacritty_to_kitty(self):
        # Parse Alacritty config
        alacritty_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        ctec = AlacrittyAdapter.parse(alacritty_path)

        # Export to Kitty
        kitty_output = KittyAdapter.export(ctec)

        # Re-parse as Kitty
        kitty_ctec = KittyAdapter.parse("test.conf", content=kitty_output)

        # Core settings should be preserved
        assert kitty_ctec.font.family == ctec.font.family

    def test_color_preservation_across_terminals(self):
        """Test that colors are preserved when converting between terminals."""
        # Start with a known color scheme
        original = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(197, 200, 198),
                background=Color(29, 31, 33),
                red=Color(204, 102, 102),
            )
        )

        # Convert through all terminals
        ghostty_output = GhosttyAdapter.export(original)
        ghostty_ctec = GhosttyAdapter.parse("test", content=ghostty_output)

        # Colors should be preserved
        assert ghostty_ctec.color_scheme.foreground.r == 197
        assert ghostty_ctec.color_scheme.foreground.g == 200
        assert ghostty_ctec.color_scheme.foreground.b == 198
