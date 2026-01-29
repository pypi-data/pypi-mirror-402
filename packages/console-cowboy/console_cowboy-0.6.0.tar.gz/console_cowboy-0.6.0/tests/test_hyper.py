"""Tests for the Hyper adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    FontWeight,
    KeyBinding,
    ScrollConfig,
    WindowConfig,
)
from console_cowboy.terminals import HyperAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestHyperAdapter:
    """Tests for the Hyper adapter."""

    def test_adapter_metadata(self):
        assert HyperAdapter.name == "hyper"
        assert HyperAdapter.display_name == "Hyper"
        assert ".js" in HyperAdapter.config_extensions
        assert ".config/Hyper/.hyper.js" in HyperAdapter.default_config_paths

    def test_can_parse(self):
        """Test format detection."""
        hyper_content = """
module.exports = {
  config: {
    fontSize: 14,
    fontFamily: 'Menlo'
  }
};
"""
        assert HyperAdapter.can_parse(hyper_content) is True

        # Non-Hyper content
        assert HyperAdapter.can_parse("font-family = Menlo") is False

    def test_parse_fixture(self):
        """Test parsing the full fixture file."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.source_terminal == "hyper"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.font.line_height == 1.2
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.cursor.blink is True

    def test_parse_font(self):
        """Test parsing font settings."""
        content = """
module.exports = {
  config: {
    fontSize: 16,
    fontFamily: 'Fira Code, Monaco, monospace',
    fontWeight: 'bold',
    lineHeight: 1.5
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.font.family == "Fira Code"
        assert ctec.font.fallback_fonts == ["Monaco", "monospace"]
        assert ctec.font.size == 16.0
        assert ctec.font.weight == FontWeight.BOLD
        assert ctec.font.line_height == 1.5

    def test_parse_cursor(self):
        """Test parsing cursor settings."""
        content = """
module.exports = {
  config: {
    cursorShape: 'BEAM',
    cursorBlink: false
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.cursor.style == CursorStyle.BEAM
        assert ctec.cursor.blink is False

    def test_parse_cursor_underline(self):
        """Test parsing underline cursor style."""
        content = """
module.exports = {
  config: {
    cursorShape: 'UNDERLINE',
    cursorBlink: true
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.cursor.style == CursorStyle.UNDERLINE
        assert ctec.cursor.blink is True

    def test_parse_colors(self):
        """Test parsing color scheme."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # Foreground: #c5c8c6
        assert ctec.color_scheme.foreground.r == 197
        assert ctec.color_scheme.foreground.g == 200
        assert ctec.color_scheme.foreground.b == 198
        # Background: #1d1f21
        assert ctec.color_scheme.background.r == 29
        assert ctec.color_scheme.background.g == 31
        assert ctec.color_scheme.background.b == 33

    def test_parse_ansi_colors(self):
        """Test parsing ANSI color palette."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # black: #282a2e
        assert ctec.color_scheme.black.r == 40
        assert ctec.color_scheme.black.g == 42
        assert ctec.color_scheme.black.b == 46
        # lightRed -> bright_red: #cc6666
        assert ctec.color_scheme.bright_red.r == 204
        assert ctec.color_scheme.bright_red.g == 102
        assert ctec.color_scheme.bright_red.b == 102

    def test_parse_behavior(self):
        """Test parsing behavior settings."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.behavior.shell == "/bin/zsh"
        assert ctec.behavior.shell_args == ["--login"]
        assert ctec.behavior.environment_variables == {"TERM": "xterm-256color"}
        assert ctec.behavior.copy_on_select is False

    def test_parse_scroll(self):
        """Test parsing scroll settings."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.scroll is not None
        assert ctec.scroll.lines == 10000

    def test_parse_window_padding(self):
        """Test parsing window padding."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert ctec.window is not None
        assert ctec.window.padding_vertical == 12
        assert ctec.window.padding_horizontal == 14

    def test_parse_keybindings(self):
        """Test parsing keybindings."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        assert len(ctec.key_bindings) == 3

        # Find the devtools binding
        devtools = next(
            (kb for kb in ctec.key_bindings if kb.action == "window:devtools"), None
        )
        assert devtools is not None
        assert devtools.key == "o"
        assert "super" in devtools.mods
        assert "alt" in devtools.mods

    def test_parse_plugins(self):
        """Test parsing plugins as terminal-specific settings."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        plugins = ctec.get_terminal_specific("hyper", "plugins")
        assert plugins is not None
        assert "hyper-snazzy" in plugins
        assert "hyper-tabs-enhanced" in plugins

    def test_parse_terminal_specific(self):
        """Test parsing Hyper-specific settings."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        ctec = HyperAdapter.parse(config_path)

        update_channel = ctec.get_terminal_specific("hyper", "updateChannel")
        assert update_channel == "stable"

        webgl = ctec.get_terminal_specific("hyper", "webGLRenderer")
        assert webgl is True

    def test_export_basic(self):
        """Test basic export functionality."""
        ctec = CTEC(
            font=FontConfig(family="Fira Code", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BEAM, blink=True),
        )
        output = HyperAdapter.export(ctec)

        assert "fontFamily: 'Fira Code'" in output
        assert "fontSize: 12" in output
        assert "cursorShape: 'BEAM'" in output
        assert "cursorBlink: true" in output
        assert "module.exports" in output

    def test_export_colors(self):
        """Test exporting color scheme."""
        ctec = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
                cursor=Color(255, 0, 0),
            )
        )
        output = HyperAdapter.export(ctec)

        assert "foregroundColor: '#ffffff'" in output
        assert "backgroundColor: '#000000'" in output
        assert "cursorColor: '#ff0000'" in output

    def test_export_ansi_colors(self):
        """Test exporting ANSI color palette."""
        ctec = CTEC(
            color_scheme=ColorScheme(
                black=Color(40, 42, 46),
                red=Color(165, 66, 66),
                bright_red=Color(204, 102, 102),
            )
        )
        output = HyperAdapter.export(ctec)

        assert "colors:" in output
        assert "black: '#282a2e'" in output
        assert "red: '#a54242'" in output
        assert "lightRed: '#cc6666'" in output

    def test_export_behavior(self):
        """Test exporting behavior settings."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                shell="/bin/bash",
                shell_args=["-l", "-c", "echo hello"],
                copy_on_select=True,
            )
        )
        output = HyperAdapter.export(ctec)

        assert "shell: '/bin/bash'" in output
        assert "shellArgs: ['-l', '-c', 'echo hello']" in output
        assert "copyOnSelect: true" in output

    def test_export_scroll(self):
        """Test exporting scroll settings."""
        ctec = CTEC(scroll=ScrollConfig(lines=5000))
        output = HyperAdapter.export(ctec)

        assert "scrollback: 5000" in output

    def test_export_keybindings(self):
        """Test exporting keybindings."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(action="tab:new", key="t", mods=["super"]),
                KeyBinding(action="window:close", key="w", mods=["super", "shift"]),
            ]
        )
        output = HyperAdapter.export(ctec)

        assert "'tab:new': 'cmd+t'" in output
        assert "'window:close': 'cmd+shift+w'" in output

    def test_export_plugins(self):
        """Test exporting plugins."""
        ctec = CTEC()
        ctec.add_terminal_specific("hyper", "plugins", ["hyper-snazzy", "hypercwd"])
        output = HyperAdapter.export(ctec)

        assert "plugins: ['hyper-snazzy', 'hypercwd']" in output

    def test_export_font_with_fallbacks(self):
        """Test exporting font with fallback fonts."""
        ctec = CTEC(
            font=FontConfig(
                family="JetBrains Mono",
                fallback_fonts=["Menlo", "DejaVu Sans Mono", "monospace"],
            )
        )
        output = HyperAdapter.export(ctec)

        assert "fontFamily:" in output
        assert "JetBrains Mono" in output
        assert "Menlo" in output

    def test_export_window_padding(self):
        """Test exporting window padding."""
        ctec = CTEC(
            window=WindowConfig(
                padding_horizontal=14,
                padding_vertical=12,
            )
        )
        output = HyperAdapter.export(ctec)

        assert "padding: '12px 14px'" in output

    def test_export_equal_padding(self):
        """Test exporting equal horizontal and vertical padding."""
        ctec = CTEC(
            window=WindowConfig(
                padding_horizontal=10,
                padding_vertical=10,
            )
        )
        output = HyperAdapter.export(ctec)

        assert "padding: '10px'" in output

    def test_roundtrip(self):
        """Test round-trip conversion."""
        config_path = FIXTURES_DIR / "hyper" / ".hyper.js"
        original = HyperAdapter.parse(config_path)

        # Export and re-parse
        exported = HyperAdapter.export(original)
        restored = HyperAdapter.parse("test.js", content=exported)

        # Check key values are preserved
        assert restored.font.family == original.font.family
        assert restored.font.size == original.font.size
        assert restored.cursor.style == original.cursor.style
        assert restored.cursor.blink == original.cursor.blink
        assert restored.behavior.shell == original.behavior.shell
        assert restored.scroll.lines == original.scroll.lines

    def test_parse_rgba_colors(self):
        """Test parsing rgba() color values."""
        content = """
module.exports = {
  config: {
    cursorColor: 'rgba(248, 28, 229, 0.8)',
    selectionColor: 'rgba(100, 150, 200, 0.5)'
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.color_scheme is not None
        assert ctec.color_scheme.cursor.r == 248
        assert ctec.color_scheme.cursor.g == 28
        assert ctec.color_scheme.cursor.b == 229
        assert ctec.color_scheme.selection.r == 100
        assert ctec.color_scheme.selection.g == 150
        assert ctec.color_scheme.selection.b == 200

    def test_parse_numeric_font_weight(self):
        """Test parsing numeric font weight."""
        content = """
module.exports = {
  config: {
    fontWeight: 600
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.font.weight == FontWeight.SEMI_BOLD

    def test_parse_single_padding(self):
        """Test parsing single value padding."""
        content = """
module.exports = {
  config: {
    padding: '16px'
  }
};
"""
        ctec = HyperAdapter.parse("test.js", content=content)

        assert ctec.window.padding_horizontal == 16
        assert ctec.window.padding_vertical == 16


class TestHyperJavaScriptParser:
    """Tests for the JavaScript parser module."""

    def test_parse_simple_config(self):
        """Test parsing a simple configuration."""
        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        js_source = """
module.exports = {
  config: {
    fontSize: 14,
    fontFamily: 'Menlo'
  }
};
"""
        result = execute_hyper_config(js_source)
        assert result["config"]["fontSize"] == 14
        assert result["config"]["fontFamily"] == "Menlo"

    def test_parse_nested_objects(self):
        """Test parsing nested objects."""
        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        js_source = """
module.exports = {
  config: {
    colors: {
      black: '#000000',
      white: '#ffffff'
    }
  }
};
"""
        result = execute_hyper_config(js_source)
        assert result["config"]["colors"]["black"] == "#000000"
        assert result["config"]["colors"]["white"] == "#ffffff"

    def test_parse_arrays(self):
        """Test parsing arrays."""
        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        js_source = """
module.exports = {
  plugins: ['plugin1', 'plugin2'],
  config: {}
};
"""
        result = execute_hyper_config(js_source)
        assert result["plugins"] == ["plugin1", "plugin2"]

    def test_parse_color_hex(self):
        """Test parsing hex colors."""
        from console_cowboy.terminals.hyper.javascript import parse_hyper_color

        assert parse_hyper_color("#ff0000") == (255, 0, 0)
        assert parse_hyper_color("#00ff00") == (0, 255, 0)
        assert parse_hyper_color("#0000ff") == (0, 0, 255)
        assert parse_hyper_color("#fff") == (255, 255, 255)
        assert parse_hyper_color("#000") == (0, 0, 0)

    def test_parse_color_rgba(self):
        """Test parsing rgba colors."""
        from console_cowboy.terminals.hyper.javascript import parse_hyper_color

        assert parse_hyper_color("rgba(255, 0, 0, 0.5)") == (255, 0, 0)
        assert parse_hyper_color("rgba(100, 150, 200, 1.0)") == (100, 150, 200)

    def test_parse_color_rgb(self):
        """Test parsing rgb colors."""
        from console_cowboy.terminals.hyper.javascript import parse_hyper_color

        assert parse_hyper_color("rgb(255, 128, 64)") == (255, 128, 64)

    def test_parse_invalid_color(self):
        """Test parsing invalid colors returns None."""
        from console_cowboy.terminals.hyper.javascript import parse_hyper_color

        assert parse_hyper_color("invalid") is None
        assert parse_hyper_color("") is None
        assert parse_hyper_color("#gggggg") is None

    def test_invalid_js_raises_error(self):
        """Test that invalid JavaScript raises an error."""
        import pytest

        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        with pytest.raises(ValueError, match="Failed to execute"):
            execute_hyper_config("this is not valid javascript {{{{")

    def test_missing_exports_raises_error(self):
        """Test that missing exports raises an error."""
        import pytest

        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        with pytest.raises(ValueError, match="did not export"):
            execute_hyper_config("var x = 1;")

    def test_config_with_percent_characters(self):
        """Test that config containing % characters doesn't cause format string errors."""
        from console_cowboy.terminals.hyper.javascript import execute_hyper_config

        # This would fail with TypeError if using % string interpolation
        js_source = """
module.exports = {
  config: {
    shell: '/bin/bash',
    shellArgs: ['-c', 'printf "%s" test']
  }
};
"""
        result = execute_hyper_config(js_source)
        assert result["config"]["shell"] == "/bin/bash"
        assert result["config"]["shellArgs"] == ["-c", 'printf "%s" test']
