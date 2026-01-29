"""Tests for the VSCode adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
)
from console_cowboy.terminals import GhosttyAdapter, VSCodeAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestVSCodeAdapter:
    """Tests for the VSCode adapter."""

    def test_adapter_metadata(self):
        assert VSCodeAdapter.name == "vscode"
        assert VSCodeAdapter.display_name == "Visual Studio Code"
        assert ".json" in VSCodeAdapter.config_extensions

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(config_path)

        assert ctec.source_terminal == "vscode"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.cursor.blink is True

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # Check foreground (#c5c8c6)
        assert ctec.color_scheme.foreground.r == 197
        assert ctec.color_scheme.foreground.g == 200
        assert ctec.color_scheme.foreground.b == 198
        # Check background (#1d1f21)
        assert ctec.color_scheme.background.r == 29
        assert ctec.color_scheme.background.g == 31
        assert ctec.color_scheme.background.b == 33

    def test_parse_scroll(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(config_path)

        assert ctec.scroll is not None
        assert ctec.scroll.lines == 10000

    def test_parse_behavior(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(config_path)

        assert ctec.behavior is not None
        assert ctec.behavior.copy_on_select is True

    def test_parse_from_content(self):
        content = """
{
    "terminal.integrated.fontFamily": "Fira Code",
    "terminal.integrated.fontSize": 16,
    "terminal.integrated.cursorStyle": "line"
}
"""
        ctec = VSCodeAdapter.parse("test.json", content=content)
        assert ctec.font.family == "Fira Code"
        assert ctec.font.size == 16.0
        assert ctec.cursor.style == CursorStyle.BEAM

    def test_export(self):
        import json

        ctec = CTEC(
            font=FontConfig(family="Fira Code", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BEAM, blink=False),
        )
        output = VSCodeAdapter.export(ctec)
        data = json.loads(output)

        assert data["terminal.integrated.fontFamily"] == "Fira Code"
        assert data["terminal.integrated.fontSize"] == 12.0
        assert data["terminal.integrated.cursorStyle"] == "line"
        assert data["terminal.integrated.cursorBlinking"] is False

    def test_export_colors(self):
        import json

        ctec = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            )
        )
        output = VSCodeAdapter.export(ctec)
        data = json.loads(output)

        assert "workbench.colorCustomizations" in data
        colors = data["workbench.colorCustomizations"]
        assert colors["terminal.foreground"] == "#ffffff"
        assert colors["terminal.background"] == "#000000"

    def test_export_produces_valid_json(self):
        import json

        ctec = CTEC(
            font=FontConfig(family="Test Font", size=14.0),
        )
        output = VSCodeAdapter.export(ctec)
        # Should not raise
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_roundtrip(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        original = VSCodeAdapter.parse(config_path)

        exported = VSCodeAdapter.export(original)
        restored = VSCodeAdapter.parse("test.json", content=exported)

        assert restored.font.family == original.font.family
        assert restored.font.size == original.font.size
        assert restored.cursor.style == original.cursor.style

    def test_terminal_specific_settings(self):
        config_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(config_path)

        vscode_specific = ctec.get_terminal_specific("vscode")
        # cursorWidth should be stored as terminal-specific
        cursor_width = next(
            (s for s in vscode_specific if s.key == "terminal.integrated.cursorWidth"),
            None,
        )
        assert cursor_width is not None
        assert cursor_width.value == 2

    def test_ghostty_to_vscode(self):
        """Test converting from Ghostty to VSCode."""

        ghostty_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(ghostty_path)

        vscode_output = VSCodeAdapter.export(ctec)
        vscode_ctec = VSCodeAdapter.parse("test.json", content=vscode_output)

        assert vscode_ctec.font.family == ctec.font.family
        assert vscode_ctec.font.size == ctec.font.size

    def test_vscode_to_ghostty(self):
        """Test converting from VSCode to Ghostty."""
        vscode_path = FIXTURES_DIR / "vscode" / "settings.json"
        ctec = VSCodeAdapter.parse(vscode_path)

        ghostty_output = GhosttyAdapter.export(ctec)
        ghostty_ctec = GhosttyAdapter.parse("test", content=ghostty_output)

        assert ghostty_ctec.font.family == ctec.font.family
        assert ghostty_ctec.font.size == ctec.font.size
