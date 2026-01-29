"""Tests for terminal emulator adapters."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    KeyBinding,
    KeyBindingScope,
    TextHintAction,
    TextHintBinding,
    TextHintConfig,
    TextHintMouseBinding,
    TextHintPrecision,
    TextHintRule,
    WindowConfig,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    ITerm2Adapter,
    KittyAdapter,
    TerminalAppAdapter,
    TerminalRegistry,
    VSCodeAdapter,
    WeztermAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTerminalRegistry:
    """Tests for the terminal registry."""

    def test_get_all_terminals(self):
        names = TerminalRegistry.get_names()
        assert "iterm2" in names
        assert "ghostty" in names
        assert "alacritty" in names
        assert "kitty" in names
        assert "wezterm" in names
        assert "vscode" in names
        assert "terminal_app" in names

    def test_get_terminal_by_name(self):
        adapter = TerminalRegistry.get("ghostty")
        assert adapter == GhosttyAdapter

    def test_get_terminal_case_insensitive(self):
        adapter = TerminalRegistry.get("GHOSTTY")
        assert adapter == GhosttyAdapter

    def test_get_unknown_terminal(self):
        adapter = TerminalRegistry.get("unknown")
        assert adapter is None

    def test_list_terminals(self):
        terminals = TerminalRegistry.list_terminals()
        assert len(terminals) == 7
        assert ITerm2Adapter in terminals
        assert VSCodeAdapter in terminals
        assert TerminalAppAdapter in terminals


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


class TestAlacrittyAdapter:
    """Tests for the Alacritty adapter."""

    def test_adapter_metadata(self):
        assert AlacrittyAdapter.name == "alacritty"
        assert ".toml" in AlacrittyAdapter.config_extensions

    def test_parse_toml_fixture(self):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        ctec = AlacrittyAdapter.parse(config_path)

        assert ctec.source_terminal == "alacritty"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40

    def test_parse_yaml_fixture(self):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.yml"
        ctec = AlacrittyAdapter.parse(config_path)

        assert ctec.source_terminal == "alacritty"
        assert ctec.font.family == "JetBrains Mono"

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        ctec = AlacrittyAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        assert ctec.color_scheme.foreground is not None
        assert ctec.color_scheme.background is not None

    def test_export_toml(self):
        ctec = CTEC(
            font=FontConfig(family="Monaco", size=13.0),
            window=WindowConfig(columns=100, rows=30),
        )
        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "Monaco" in output
        assert "columns = 100" in output

    def test_export_yaml(self):
        ctec = CTEC(
            font=FontConfig(family="Monaco", size=13.0),
        )
        output = AlacrittyAdapter.export(ctec, use_toml=False)

        assert "Monaco" in output
        assert ":" in output  # YAML uses colons

    def test_key_bindings(self):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        ctec = AlacrittyAdapter.parse(config_path)

        assert len(ctec.key_bindings) > 0
        # Check for Copy binding
        copy_binding = next(
            (kb for kb in ctec.key_bindings if kb.action == "Copy"), None
        )
        assert copy_binding is not None

    def test_parse_modern_terminal_shell(self):
        """Test parsing shell from modern [terminal.shell] location (Alacritty 0.13+)."""
        config = """
[terminal.shell]
program = "/usr/local/bin/fish"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.shell == "/usr/local/bin/fish"

    def test_parse_legacy_shell_fallback(self):
        """Test parsing shell from legacy [shell] location still works."""
        config = """
[shell]
program = "/bin/bash"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.shell == "/bin/bash"

    def test_parse_modern_shell_takes_precedence(self):
        """Modern [terminal.shell] takes precedence over legacy [shell]."""
        config = """
[terminal.shell]
program = "/usr/local/bin/fish"

[shell]
program = "/bin/bash"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=config)
        assert ctec.behavior.shell == "/usr/local/bin/fish"

    def test_export_toml_uses_modern_terminal_shell(self):
        """Export to TOML should use modern [terminal.shell] location."""
        from console_cowboy.ctec.schema import BehaviorConfig

        ctec = CTEC(behavior=BehaviorConfig(shell="/bin/zsh"))
        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[terminal.shell]" in output or 'terminal.shell' in output
        assert "program" in output
        assert "/bin/zsh" in output

    def test_export_yaml_uses_legacy_shell(self):
        """Export to YAML should use legacy [shell] location for backwards compatibility."""
        from console_cowboy.ctec.schema import BehaviorConfig

        ctec = CTEC(behavior=BehaviorConfig(shell="/bin/zsh"))
        output = AlacrittyAdapter.export(ctec, use_toml=False)

        # YAML format should use legacy shell key
        assert "shell:" in output
        assert "program:" in output
        assert "/bin/zsh" in output


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


class TestWeztermAdapter:
    """Tests for the Wezterm adapter."""

    def test_adapter_metadata(self):
        assert WeztermAdapter.name == "wezterm"
        assert ".lua" in WeztermAdapter.config_extensions

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        ctec = WeztermAdapter.parse(config_path)

        assert ctec.source_terminal == "wezterm"
        assert ctec.font.family == "JetBrains Mono"
        assert ctec.font.size == 14.0
        assert ctec.window.columns == 120
        assert ctec.window.rows == 40

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        ctec = WeztermAdapter.parse(config_path)

        assert ctec.color_scheme is not None
        # With proper Lua execution, we no longer need warnings about complexity
        assert len(ctec.warnings) == 0

    def test_parse_cursor(self):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        ctec = WeztermAdapter.parse(config_path)

        assert ctec.cursor is not None
        assert ctec.cursor.style == CursorStyle.BLOCK
        assert ctec.cursor.blink is True

    def test_export(self):
        ctec = CTEC(
            font=FontConfig(family="Fira Code", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BEAM, blink=False),
        )
        output = WeztermAdapter.export(ctec)

        assert 'wezterm.font("Fira Code")' in output
        assert "font_size = 12.0" in output
        assert "SteadyBar" in output

    def test_export_colors(self):
        ctec = CTEC(
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            )
        )
        output = WeztermAdapter.export(ctec)

        assert 'foreground = "#ffffff"' in output
        assert 'background = "#000000"' in output

    def test_export_valid_lua(self):
        """Verify the exported Lua is syntactically valid."""
        ctec = CTEC(
            font=FontConfig(family="Test", size=12.0),
            window=WindowConfig(columns=80, rows=24),
        )
        output = WeztermAdapter.export(ctec)

        # Should have required Lua structure
        assert "local wezterm = require 'wezterm'" in output
        assert "local config = wezterm.config_builder()" in output
        assert "return config" in output

    def test_parse_color_scheme_name(self):
        """Test parsing config.color_scheme = 'Dracula'."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme = 'Dracula'

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        assert ctec.color_scheme is not None
        assert ctec.color_scheme.name == "Dracula"

    def test_export_color_scheme_name(self):
        """Test exporting color scheme by name."""
        ctec = CTEC(color_scheme=ColorScheme(name="Gruvbox Dark"))
        output = WeztermAdapter.export(ctec)

        assert 'config.color_scheme = "Gruvbox Dark"' in output

    def test_parse_harfbuzz_features_disables_ligatures(self):
        """Test that harfbuzz_features with liga=0 sets ligatures=False."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.font = wezterm.font("JetBrains Mono", {
    harfbuzz_features = { "liga=0", "calt=0" }
})

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        assert ctec.font is not None
        assert ctec.font.ligatures is False

    def test_parse_leader_key(self):
        """Test parsing config.leader configuration."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.leader = { key = 'a', mods = 'CTRL', timeout_milliseconds = 1000 }

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        leader_settings = [s for s in ctec.terminal_specific if s.key == "leader"]
        assert len(leader_settings) == 1
        assert leader_settings[0].value["key"] == "a"
        assert leader_settings[0].value["mods"] == "CTRL"

    def test_parse_event_callbacks_warning(self):
        """Test that wezterm.on() callbacks generate a warning."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

wezterm.on('update-right-status', function(window, pane)
    window:set_right_status('test')
end)

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        assert any("event callbacks" in w.lower() for w in ctec.warnings)
        assert any("update-right-status" in w for w in ctec.warnings)

    def test_export_action_syntax_copyto(self):
        """Test that CopyTo action exports with correct syntax."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="CopyTo", key="c", mods=["CTRL"], action_param="Clipboard"
                )
            ]
        )
        output = WeztermAdapter.export(ctec)

        assert 'wezterm.action.CopyTo("Clipboard")' in output

    def test_export_action_syntax_split_horizontal(self):
        """Test that SplitHorizontal action exports with table syntax."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="SplitHorizontal",
                    key="s",
                    mods=["CTRL"],
                    action_param="CurrentPaneDomain",
                )
            ]
        )
        output = WeztermAdapter.export(ctec)

        assert "SplitHorizontal" in output
        assert "domain" in output

    def test_sandbox_blocks_os_execute(self):
        """Test that the Lua sandbox blocks dangerous os.execute calls."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- This should fail because os is not available in the sandbox
os.execute('echo pwned')

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        # Should have a warning about the sandbox blocking os access
        assert any("Failed to execute" in w or "os" in w.lower() for w in ctec.warnings)

    def test_sandbox_blocks_io_open(self):
        """Test that the Lua sandbox blocks dangerous io.open calls."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- This should fail because io is not available in the sandbox
local f = io.open('/etc/passwd', 'r')

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        # Should have a warning about the sandbox blocking io access
        assert any("Failed to execute" in w or "io" in w.lower() for w in ctec.warnings)

    def test_sandbox_blocks_loadfile(self):
        """Test that the Lua sandbox blocks dangerous loadfile calls."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- This should fail because loadfile is not available in the sandbox
local evil = loadfile('/tmp/evil.lua')

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        # Should have a warning about the sandbox blocking loadfile
        assert any("Failed to execute" in w for w in ctec.warnings)

    def test_sandbox_allows_safe_operations(self):
        """Test that the sandbox allows legitimate WezTerm config operations."""
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- Safe string operations
local font_name = string.upper("jetbrains mono")

-- Safe table operations
local colors = {}
table.insert(colors, "#ff0000")

-- Safe math operations
local size = math.floor(12.5)

config.font_size = size

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        # Should parse successfully without errors
        assert not any("Failed to execute" in w for w in ctec.warnings)
        assert ctec.font is not None
        assert ctec.font.size == 12


class TestITerm2Adapter:
    """Tests for the iTerm2 adapter."""

    def test_adapter_metadata(self):
        assert ITerm2Adapter.name == "iterm2"
        assert ".plist" in ITerm2Adapter.config_extensions

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        assert ctec.source_terminal == "iterm2"
        assert ctec.window.columns == 120
        assert ctec.window.rows == 200

    def test_parse_default_profile(self):
        """Test that the default profile settings are imported correctly."""
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        # Settings from the default profile should be at the CTEC level
        assert ctec.color_scheme is not None
        assert ctec.font is not None or ctec.cursor is not None

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        assert ctec.color_scheme is not None
        assert ctec.color_scheme.foreground is not None

    def test_export(self):
        ctec = CTEC(
            font=FontConfig(family="Monaco", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BLOCK, blink=True),
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            ),
        )
        output = ITerm2Adapter.export(ctec)

        # Should be valid plist XML
        assert '<?xml version="1.0"' in output
        assert "<plist" in output
        assert "Monaco" in output

    def test_terminal_specific_settings(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        iterm_specific = ctec.get_terminal_specific("iterm2")
        assert len(iterm_specific) > 0

    def test_hotkey_profile_extraction(self):
        """Test that hotkey settings are extracted from a separate Hotkey Window profile."""
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        # The Default profile doesn't have hotkey settings, but the Hotkey Window profile does
        # The adapter should extract hotkey settings from the Hotkey Window profile
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.enabled is True
        assert ctec.quick_terminal.floating is True
        assert ctec.quick_terminal.animation_duration == 200
        assert ctec.quick_terminal.hotkey_key_code == 7  # 'X' key
        assert ctec.quick_terminal.hotkey_modifiers == 1441792  # Cmd+Option
        # Window Type 7 = Full Height Right of Screen
        from console_cowboy.ctec.schema import QuickTerminalPosition

        assert ctec.quick_terminal.position == QuickTerminalPosition.RIGHT


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
        import pytest

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


class TestTextHints:
    """Tests for text hints/smart selection configuration."""

    def test_alacritty_parse_hints(self):
        """Test parsing Alacritty hints from TOML content."""
        content = """
[hints]
alphabet = "jfkdls;ahgurieowpq"

[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "xdg-open"
post_processing = true
binding = { key = "U", mods = "Control+Shift" }
mouse = { mods = "Control", enabled = true }

[[hints.enabled]]
regex = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+"
action = "Copy"
binding = { key = "E", mods = "Control+Shift" }
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        assert ctec.text_hints is not None
        assert ctec.text_hints.enabled is True
        assert ctec.text_hints.alphabet == "jfkdls;ahgurieowpq"
        assert len(ctec.text_hints.rules) == 2

        # First rule - URL hint
        rule1 = ctec.text_hints.rules[0]
        assert "https" in rule1.regex
        assert rule1.hyperlinks is True
        assert rule1.command == "xdg-open"
        assert rule1.post_processing is True
        assert rule1.binding.key == "U"
        assert "Control" in rule1.binding.mods
        assert rule1.mouse.enabled is True

        # Second rule - email hint
        rule2 = ctec.text_hints.rules[1]
        assert "@" in rule2.regex
        assert rule2.action == TextHintAction.COPY

    def test_alacritty_export_hints(self):
        """Test exporting hints to Alacritty format."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                alphabet="asdfgh",
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        hyperlinks=True,
                        command="open",
                        post_processing=True,
                        binding=TextHintBinding(key="O", mods=["Control", "Shift"]),
                        mouse=TextHintMouseBinding(mods=["Control"], enabled=True),
                    ),
                    TextHintRule(
                        regex="\\d{4}-\\d{2}-\\d{2}",
                        action=TextHintAction.COPY,
                    ),
                ],
            )
        )

        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[hints]" in output
        assert 'alphabet = "asdfgh"' in output
        assert "[[hints.enabled]]" in output
        assert "https?://" in output
        assert 'command = "open"' in output
        assert "post_processing = true" in output

    def test_alacritty_hints_roundtrip(self):
        """Test Alacritty hints survive round-trip conversion."""
        content = """
[hints]
alphabet = "jfkdls"

[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "open"
post_processing = true
binding = { key = "O", mods = "Control+Shift" }
"""
        original = AlacrittyAdapter.parse("test.toml", content=content)
        exported = AlacrittyAdapter.export(original, use_toml=True)
        restored = AlacrittyAdapter.parse("test.toml", content=exported)

        assert restored.text_hints is not None
        assert restored.text_hints.alphabet == original.text_hints.alphabet
        assert len(restored.text_hints.rules) == len(original.text_hints.rules)

        orig_rule = original.text_hints.rules[0]
        rest_rule = restored.text_hints.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.hyperlinks == orig_rule.hyperlinks
        assert rest_rule.command == orig_rule.command
        assert rest_rule.post_processing == orig_rule.post_processing

    def test_iterm2_parse_smart_selection(self):
        """Test parsing iTerm2 Smart Selection Rules from plist content."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Smart Selection Rules": [
                {
                    "regex": "(https?://|www\\.)[^\\s]+",
                    "precision": 3,  # HIGH
                    "notes": "URL detection",
                    "actions": [{"title": "Open URL", "action": ""}],
                },
                {
                    "regex": "/[a-zA-Z0-9._/-]+",
                    "precision": 2,  # NORMAL
                    "notes": "File path detection",
                    "actions": [{"title": "Run Command...", "action": "open -R \\0"}],
                },
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)

        assert ctec.text_hints is not None
        assert ctec.text_hints.enabled is True
        assert len(ctec.text_hints.rules) == 2

        # First rule - URL
        rule1 = ctec.text_hints.rules[0]
        assert "https" in rule1.regex
        assert rule1.precision == TextHintPrecision.HIGH
        assert rule1.notes == "URL detection"
        assert rule1.action == TextHintAction.OPEN_URL

        # Second rule - file path
        rule2 = ctec.text_hints.rules[1]
        assert "/" in rule2.regex
        assert rule2.precision == TextHintPrecision.NORMAL
        assert rule2.action == TextHintAction.RUN_COMMAND
        assert rule2.parameter == "open -R \\0"

    def test_iterm2_export_smart_selection(self):
        """Test exporting text hints to iTerm2 Smart Selection Rules."""
        import plistlib

        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        precision=TextHintPrecision.HIGH,
                        notes="URL detection",
                        action=TextHintAction.OPEN_URL,
                    ),
                    TextHintRule(
                        regex="/[a-zA-Z0-9._/-]+",
                        precision=TextHintPrecision.NORMAL,
                        notes="File path",
                        action=TextHintAction.RUN_COMMAND,
                        command="open -R",
                    ),
                ],
            )
        )

        output = ITerm2Adapter.export(ctec)
        data = plistlib.loads(output.encode())

        profile = data["New Bookmarks"][0]
        assert "Smart Selection Rules" in profile

        rules = profile["Smart Selection Rules"]
        assert len(rules) == 2

        assert "https" in rules[0]["regex"]
        assert rules[0]["precision"] == 3  # HIGH
        assert rules[0]["actions"][0]["title"] == "Open URL"

    def test_iterm2_smart_selection_roundtrip(self):
        """Test iTerm2 Smart Selection Rules survive round-trip."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Default Bookmark": "Yes",
            "Smart Selection Rules": [
                {
                    "regex": "(https?://)[^\\s]+",
                    "precision": 4,  # VERY_HIGH
                    "notes": "HTTP URL",
                    "actions": [{"title": "Open URL", "action": ""}],
                }
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        original = ITerm2Adapter.parse("test.plist", content=content)
        exported = ITerm2Adapter.export(original)
        restored = ITerm2Adapter.parse("test.plist", content=exported)

        assert restored.text_hints is not None
        assert len(restored.text_hints.rules) == len(original.text_hints.rules)

        orig_rule = original.text_hints.rules[0]
        rest_rule = restored.text_hints.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.precision == orig_rule.precision
        assert rest_rule.action == orig_rule.action

    def test_alacritty_to_iterm2_hints(self):
        """Test converting hints from Alacritty to iTerm2."""
        import plistlib

        alacritty_content = """
[hints]
[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "open"
post_processing = true
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=alacritty_content)

        iterm_output = ITerm2Adapter.export(ctec)
        iterm_data = plistlib.loads(iterm_output.encode())

        profile = iterm_data["New Bookmarks"][0]
        assert "Smart Selection Rules" in profile

        rules = profile["Smart Selection Rules"]
        assert len(rules) == 1
        assert "https" in rules[0]["regex"]

    def test_iterm2_to_alacritty_hints(self):
        """Test converting hints from iTerm2 to Alacritty."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Smart Selection Rules": [
                {
                    "regex": "https?://[^\\s]+",
                    "precision": 3,
                    "actions": [{"title": "Copy", "action": ""}],
                }
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)
        alacritty_output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[hints]" in alacritty_output
        # tomli_w outputs inline tables, not [[hints.enabled]] syntax
        assert "enabled = [" in alacritty_output
        assert "https" in alacritty_output
        assert "Copy" in alacritty_output

    def test_kitty_warns_about_unsupported_hints(self):
        """Test that Kitty export warns about unsupported hints."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(regex="https?://[^\\s]+"),
                    TextHintRule(regex="[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+"),
                ],
            )
        )

        KittyAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("hint" in w.lower() for w in ctec.warnings)
        assert any("2" in w for w in ctec.warnings)  # Number of rules

    def test_ghostty_warns_about_unsupported_hints(self):
        """Test that Ghostty export warns about unsupported hints."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[TextHintRule(regex="https?://[^\\s]+")],
            )
        )

        GhosttyAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("hint" in w.lower() for w in ctec.warnings)

    def test_wezterm_exports_hyperlink_rules(self):
        """Test that WezTerm exports URL hints as hyperlink_rules."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        action=TextHintAction.OPEN,
                        hyperlinks=True,
                    )
                ],
            )
        )

        output = WeztermAdapter.export(ctec)

        assert "hyperlink_rules" in output
        assert "wezterm.default_hyperlink_rules()" in output
        assert "table.insert" in output
        assert "https" in output

    def test_wezterm_warns_about_non_url_hints(self):
        """Test that WezTerm warns about hints with non-URL actions."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="[a-z]+@[a-z]+",
                        action=TextHintAction.COPY,  # Can't be a hyperlink
                    )
                ],
            )
        )

        WeztermAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("Copy" in w or "action" in w.lower() for w in ctec.warnings)

    def test_wezterm_parses_hyperlink_rules(self):
        """Test that WezTerm parses hyperlink_rules into text hints.

        Uses a Lua interpreter with a mock wezterm object for accurate parsing.
        """
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.hyperlink_rules = {
  { regex = [[https?://[^\\s]+]], format = "$0" },
  { regex = "task-(\\\\d+)", format = "https://example.com/task/$1" },
}

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        assert ctec.text_hints is not None
        assert len(ctec.text_hints.rules) == 2
        assert ctec.text_hints.rules[0].regex == "https?://[^\\s]+"
        assert ctec.text_hints.rules[0].action == TextHintAction.OPEN
        assert ctec.text_hints.rules[1].parameter == "https://example.com/task/$1"

    def test_text_hint_config_serialization(self):
        """Test TextHintConfig to_dict and from_dict."""
        config = TextHintConfig(
            enabled=True,
            alphabet="asdfgh",
            rules=[
                TextHintRule(
                    regex="https?://[^\\s]+",
                    hyperlinks=True,
                    action=TextHintAction.OPEN,
                    command="open",
                    post_processing=True,
                    persist=False,
                    binding=TextHintBinding(key="O", mods=["Control", "Shift"]),
                    mouse=TextHintMouseBinding(mods=["Control"], enabled=True),
                    precision=TextHintPrecision.HIGH,
                    notes="URL detection",
                    parameter="\\0",
                )
            ],
        )

        dict_repr = config.to_dict()
        restored = TextHintConfig.from_dict(dict_repr)

        assert restored.enabled == config.enabled
        assert restored.alphabet == config.alphabet
        assert len(restored.rules) == 1

        orig_rule = config.rules[0]
        rest_rule = restored.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.hyperlinks == orig_rule.hyperlinks
        assert rest_rule.action == orig_rule.action
        assert rest_rule.command == orig_rule.command
        assert rest_rule.post_processing == orig_rule.post_processing
        assert rest_rule.persist == orig_rule.persist
        assert rest_rule.binding.key == orig_rule.binding.key
        assert rest_rule.binding.mods == orig_rule.binding.mods
        assert rest_rule.mouse.mods == orig_rule.mouse.mods
        assert rest_rule.mouse.enabled == orig_rule.mouse.enabled
        assert rest_rule.precision == orig_rule.precision
        assert rest_rule.notes == orig_rule.notes
        assert rest_rule.parameter == orig_rule.parameter


class TestKeyBindings:
    """Tests for keybinding parsing and export across terminals."""

    def test_ghostty_parse_basic_keybindings(self):
        """Test parsing basic Ghostty keybindings."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = ctrl+shift+v=paste_from_clipboard
keybind = ctrl+t=new_tab
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 3

        # Check first binding
        kb1 = ctec.key_bindings[0]
        assert kb1.action == "copy_to_clipboard"
        assert kb1.key == "c"
        assert "ctrl" in kb1.mods
        assert "shift" in kb1.mods

        # Check third binding (no modifiers except ctrl)
        kb3 = ctec.key_bindings[2]
        assert kb3.action == "new_tab"
        assert kb3.key == "t"
        assert kb3.mods == ["ctrl"]

    def test_ghostty_parse_action_with_parameter(self):
        """Test parsing Ghostty keybindings with action parameters."""
        content = """
keybind = ctrl+shift+enter=new_split:right
keybind = ctrl+shift+minus=new_split:down
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 2

        kb1 = ctec.key_bindings[0]
        assert kb1.action == "new_split"
        assert kb1.action_param == "right"
        assert kb1.get_full_action() == "new_split:right"

        kb2 = ctec.key_bindings[1]
        assert kb2.action == "new_split"
        assert kb2.action_param == "down"

    def test_ghostty_parse_global_keybinding(self):
        """Test parsing Ghostty global keybindings."""
        content = """
keybind = global:ctrl+grave=toggle_quick_terminal
keybind = global:super+space=toggle_quick_terminal
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 2

        kb1 = ctec.key_bindings[0]
        assert kb1.scope == KeyBindingScope.GLOBAL
        assert kb1.action == "toggle_quick_terminal"
        assert kb1.key == "grave"
        assert kb1.mods == ["ctrl"]

    def test_ghostty_parse_unconsumed_keybinding(self):
        """Test parsing Ghostty unconsumed keybindings."""
        content = """
keybind = unconsumed:ctrl+shift+g=write_screen_file
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.scope == KeyBindingScope.UNCONSUMED
        assert kb.consume is False
        assert kb.action == "write_screen_file"

    def test_ghostty_parse_key_sequence(self):
        """Test parsing Ghostty key sequences (leader keys)."""
        content = """
keybind = ctrl+a>n=new_window
keybind = ctrl+a>t=new_tab
keybind = ctrl+b>ctrl+c=close_tab
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 3

        # First key sequence
        kb1 = ctec.key_bindings[0]
        assert kb1.key_sequence == ["ctrl+a", "n"]
        assert kb1.action == "new_window"
        # The key/mods represent the last key in the sequence
        assert kb1.key == "n"
        assert kb1.mods == []

        # Third key sequence with modifier on second key
        kb3 = ctec.key_bindings[2]
        assert kb3.key_sequence == ["ctrl+b", "ctrl+c"]
        assert kb3.key == "c"
        assert kb3.mods == ["ctrl"]

    def test_ghostty_parse_physical_key(self):
        """Test parsing Ghostty physical key bindings."""
        content = """
keybind = physical:ctrl+grave=toggle_quick_terminal
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.physical_key is True
        assert kb.action == "toggle_quick_terminal"

    def test_ghostty_parse_all_scope(self):
        """Test parsing Ghostty 'all:' scope keybindings."""
        content = """
keybind = all:ctrl+shift+p=command_palette
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.scope == KeyBindingScope.ALL
        assert kb.action == "command_palette"

    def test_ghostty_parse_unbind(self):
        """Test that Ghostty unbind keybindings are stored as terminal-specific."""
        content = """
keybind = ctrl+c=unbind
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        # Unbind should not create a KeyBinding
        assert len(ctec.key_bindings) == 0

        # Should be stored as terminal-specific
        ghostty_specific = ctec.get_terminal_specific("ghostty")
        unbind_settings = [s for s in ghostty_specific if "keybind_unbind" in s.key]
        assert len(unbind_settings) == 1

    def test_ghostty_export_basic_keybindings(self):
        """Test exporting basic keybindings to Ghostty format."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(action="copy_to_clipboard", key="c", mods=["ctrl", "shift"]),
                KeyBinding(
                    action="paste_from_clipboard", key="v", mods=["ctrl", "shift"]
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+c=copy_to_clipboard" in output
        assert "keybind = ctrl+shift+v=paste_from_clipboard" in output

    def test_ghostty_export_action_with_parameter(self):
        """Test exporting keybindings with action parameters."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_split",
                    key="enter",
                    mods=["ctrl", "shift"],
                    action_param="right",
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+enter=new_split:right" in output

    def test_ghostty_export_global_keybinding(self):
        """Test exporting global keybindings."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = global:ctrl+grave=toggle_quick_terminal" in output

    def test_ghostty_export_key_sequence(self):
        """Test exporting key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+a>n=new_window" in output

    def test_ghostty_keybinding_roundtrip(self):
        """Test that Ghostty keybindings survive round-trip conversion."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = global:ctrl+grave=toggle_quick_terminal
keybind = ctrl+shift+enter=new_split:right
keybind = ctrl+a>n=new_window
"""
        original = GhosttyAdapter.parse("test", content=content)
        exported = GhosttyAdapter.export(original)
        restored = GhosttyAdapter.parse("test", content=exported)

        assert len(restored.key_bindings) == len(original.key_bindings)

        # Check specific bindings are preserved
        for i, (orig, rest) in enumerate(
            zip(original.key_bindings, restored.key_bindings, strict=False)
        ):
            assert rest.action == orig.action, f"Action mismatch at index {i}"
            assert rest.key == orig.key, f"Key mismatch at index {i}"
            assert rest.mods == orig.mods, f"Mods mismatch at index {i}"
            assert rest.action_param == orig.action_param, (
                f"Param mismatch at index {i}"
            )
            assert rest.scope == orig.scope, f"Scope mismatch at index {i}"

    def test_ghostty_fixture_keybindings(self):
        """Test parsing keybindings from the Ghostty fixture file."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(config_path)

        assert len(ctec.key_bindings) > 0

        # Check for global keybinding
        global_kb = next(
            (kb for kb in ctec.key_bindings if kb.scope == KeyBindingScope.GLOBAL),
            None,
        )
        assert global_kb is not None
        assert global_kb.action == "toggle_quick_terminal"

        # Check for action with parameter
        param_kb = next(
            (kb for kb in ctec.key_bindings if kb.action_param is not None), None
        )
        assert param_kb is not None
        assert param_kb.action == "new_split"
        assert param_kb.action_param == "right"

        # Check for key sequence
        seq_kb = next(
            (kb for kb in ctec.key_bindings if kb.key_sequence is not None), None
        )
        assert seq_kb is not None
        assert "ctrl+a" in seq_kb.key_sequence

    def test_alacritty_keybindings_with_mode(self):
        """Test Alacritty keybindings with mode field."""
        content = """
[[keyboard.bindings]]
key = "V"
mods = "Control+Shift"
action = "Paste"
mode = "~Vi"

[[keyboard.bindings]]
key = "Escape"
action = "ToggleViMode"
mode = "~Vi"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        assert len(ctec.key_bindings) == 2

        # Check mode is parsed
        kb1 = ctec.key_bindings[0]
        assert kb1.mode == "~Vi"
        assert kb1.action == "Paste"

        kb2 = ctec.key_bindings[1]
        assert kb2.mode == "~Vi"

    def test_alacritty_export_keybindings_with_mode(self):
        """Test Alacritty exports keybindings with mode field."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="V",
                    mods=["Control", "Shift"],
                    mode="~Vi",
                ),
            ]
        )
        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert 'mode = "~Vi"' in output

    def test_kitty_keybinding_export_with_action_param(self):
        """Test Kitty exports keybindings with action parameters (space-separated)."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="enter",
                    mods=["ctrl", "shift"],
                    action_param="--cwd=current",
                ),
            ]
        )
        output = KittyAdapter.export(ctec)

        # Kitty uses space-separated action parameters, not colon
        assert "map ctrl+shift+enter new_window --cwd=current" in output

    def test_keybinding_schema_serialization(self):
        """Test KeyBinding to_dict and from_dict with all fields."""
        kb = KeyBinding(
            action="new_split",
            key="enter",
            mods=["ctrl", "shift"],
            action_param="right",
            scope=KeyBindingScope.GLOBAL,
            key_sequence=["ctrl+a", "n"],
            mode="~Vi",
            physical_key=True,
            consume=False,
            _raw="global:ctrl+shift+enter=new_split:right",
        )

        dict_repr = kb.to_dict()
        restored = KeyBinding.from_dict(dict_repr)

        assert restored.action == kb.action
        assert restored.key == kb.key
        assert restored.mods == kb.mods
        assert restored.action_param == kb.action_param
        assert restored.scope == kb.scope
        assert restored.key_sequence == kb.key_sequence
        assert restored.mode == kb.mode
        assert restored.physical_key == kb.physical_key
        assert restored.consume == kb.consume
        assert restored._raw == kb._raw

    def test_cross_terminal_keybinding_conversion_ghostty_to_alacritty(self):
        """Test converting keybindings from Ghostty to Alacritty."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = ctrl+shift+v=paste_from_clipboard
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        alacritty_output = AlacrittyAdapter.export(ctec, use_toml=True)

        # Check that keybindings are in the output
        assert "keyboard" in alacritty_output
        assert "bindings" in alacritty_output
        assert "copy_to_clipboard" in alacritty_output
        assert "paste_from_clipboard" in alacritty_output

    def test_cross_terminal_keybinding_conversion_alacritty_to_ghostty(self):
        """Test converting keybindings from Alacritty to Ghostty."""
        content = """
[[keyboard.bindings]]
key = "V"
mods = "Control+Shift"
action = "Paste"

[[keyboard.bindings]]
key = "C"
mods = "Control+Shift"
action = "Copy"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        ghostty_output = GhosttyAdapter.export(ctec)

        assert "keybind = " in ghostty_output
        assert "Paste" in ghostty_output
        assert "Copy" in ghostty_output

    def test_cross_terminal_keybinding_kitty_to_ghostty(self):
        """Test converting keybindings from Kitty to Ghostty."""
        content = """
map ctrl+shift+c copy_to_clipboard
map ctrl+shift+v paste_from_clipboard
"""
        ctec = KittyAdapter.parse("test.conf", content=content)

        ghostty_output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+c=copy_to_clipboard" in ghostty_output
        assert "keybind = ctrl+shift+v=paste_from_clipboard" in ghostty_output

    def test_alacritty_keybinding_with_chars_field(self):
        """Test Alacritty keybindings using chars field are preserved as terminal-specific."""
        content = """
[[keyboard.bindings]]
key = "T"
mods = "Control+Shift"
chars = "\\x1b[13;5u"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        # chars-based binding should not be in key_bindings
        assert len(ctec.key_bindings) == 0

        # But should be in terminal_specific with a warning
        specific = ctec.get_terminal_specific("alacritty")
        assert len(specific) == 1
        assert "chars:" in specific[0].key
        # TOML parser interprets escape sequences, so the actual escape character is stored
        assert "\x1b[13;5u" in specific[0].value

        # Warning should be added
        assert len(ctec.warnings) == 1
        assert "chars" in ctec.warnings[0]

    def test_alacritty_keybinding_with_command_field(self):
        """Test Alacritty keybindings using command field are preserved as terminal-specific."""
        content = """
[[keyboard.bindings]]
key = "N"
mods = "Control+Shift"
command = "alacritty msg create-window"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        # command-based binding should not be in key_bindings
        assert len(ctec.key_bindings) == 0

        # But should be in terminal_specific with a warning
        specific = ctec.get_terminal_specific("alacritty")
        assert len(specific) == 1
        assert "command:" in specific[0].key

        # Warning should be added
        assert len(ctec.warnings) == 1
        assert "command" in ctec.warnings[0]

    def test_kitty_parse_key_sequence(self):
        """Test Kitty parses key sequences (leader keys) with > separator."""
        content = """
map ctrl+a>n new_window
map ctrl+x>ctrl+y>z some_action
"""
        ctec = KittyAdapter.parse("test.conf", content=content)

        assert len(ctec.key_bindings) == 2

        # First keybinding: ctrl+a>n
        kb1 = ctec.key_bindings[0]
        assert kb1.key_sequence == ["ctrl+a", "n"]
        assert kb1.action == "new_window"
        assert kb1.key == "n"
        assert kb1.mods == []

        # Second keybinding: ctrl+x>ctrl+y>z
        kb2 = ctec.key_bindings[1]
        assert kb2.key_sequence == ["ctrl+x", "ctrl+y", "z"]
        assert kb2.action == "some_action"
        assert kb2.key == "z"
        assert kb2.mods == []

    def test_kitty_export_key_sequence(self):
        """Test Kitty exports key sequences correctly."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        output = KittyAdapter.export(ctec)

        assert "map ctrl+a>n new_window" in output

    def test_alacritty_export_warns_about_key_sequences(self):
        """Test Alacritty export warns when keybindings have key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        AlacrittyAdapter.export(ctec)

        # Warning should be added about unsupported key sequences
        assert len(ctec.warnings) == 1
        assert "key sequence" in ctec.warnings[0].lower()
        assert "ctrl+a>n" in ctec.warnings[0]

    def test_alacritty_export_warns_about_global_scope(self):
        """Test Alacritty export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        AlacrittyAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()

    def test_kitty_export_warns_about_global_scope(self):
        """Test Kitty export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        KittyAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()

    def test_kitty_export_warns_about_mode_restrictions(self):
        """Test Kitty export warns when keybindings have mode restrictions."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="v",
                    mods=["ctrl", "shift"],
                    mode="~Vi",
                ),
            ]
        )
        KittyAdapter.export(ctec)

        # Warning should be added about unsupported mode
        assert len(ctec.warnings) == 1
        assert "mode" in ctec.warnings[0].lower()
        assert "~Vi" in ctec.warnings[0]

    def test_ghostty_export_warns_about_mode_restrictions(self):
        """Test Ghostty export warns when keybindings have mode restrictions."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="v",
                    mods=["ctrl", "shift"],
                    mode="~Vi",
                ),
            ]
        )
        GhosttyAdapter.export(ctec)

        # Warning should be added about unsupported mode
        assert len(ctec.warnings) == 1
        assert "mode" in ctec.warnings[0].lower()

    def test_wezterm_export_warns_about_key_sequences(self):
        """Test WezTerm export warns when keybindings have key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="NewWindow",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        WeztermAdapter.export(ctec)

        # Warning should be added about unsupported key sequences
        assert len(ctec.warnings) == 1
        assert "key sequence" in ctec.warnings[0].lower()

    def test_wezterm_export_warns_about_global_scope(self):
        """Test WezTerm export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="ToggleQuickTerminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        WeztermAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()


class TestTabsAndPanes:
    """Tests for tab and pane configuration across terminals."""

    def test_ghostty_parse_tabs(self):
        """Test Ghostty parses tab settings."""
        config = """
window-show-tab-bar = always
gtk-tabs-location = bottom
window-new-tab-position = end
window-inherit-working-directory = true
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.visibility.value == "always"
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.new_tab_position.value == "end"
        assert ctec.tabs.inherit_working_directory is True

    def test_ghostty_parse_panes(self):
        """Test Ghostty parses pane settings."""
        config = """
unfocused-split-opacity = 0.8
unfocused-split-fill = #333333
split-divider-color = #444444
focus-follows-mouse = true
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.8
        assert ctec.panes.inactive_dim_color.to_hex() == "#333333"
        assert ctec.panes.divider_color.to_hex() == "#444444"
        assert ctec.panes.focus_follows_mouse is True

    def test_ghostty_export_tabs(self):
        """Test Ghostty exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarVisibility,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                visibility=TabBarVisibility.AUTO,
                position=TabBarPosition.BOTTOM,
                inherit_working_directory=True,
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "window-show-tab-bar = auto" in output
        assert "gtk-tabs-location = bottom" in output
        assert "window-inherit-working-directory = true" in output

    def test_ghostty_export_panes_clamps_dim_factor(self):
        """Test Ghostty clamps dim factor to minimum 0.15."""
        from console_cowboy.ctec.schema import PaneConfig

        ctec = CTEC(panes=PaneConfig(inactive_dim_factor=0.1))
        output = GhosttyAdapter.export(ctec)
        assert "unfocused-split-opacity = 0.15" in output
        assert any("0.15" in w and "clamp" in w.lower() for w in ctec.warnings)

    def test_kitty_parse_tabs(self):
        """Test Kitty parses tab settings."""
        config = """
tab_bar_edge bottom
tab_bar_style powerline
tab_bar_align center
tab_bar_min_tabs 2
tab_switch_strategy previous
active_tab_foreground #ffffff
active_tab_background #000000
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.style.value == "powerline"
        # Kitty-specific settings are stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "tab_bar_align") == "center"
        assert ctec.get_terminal_specific("kitty", "tab_switch_strategy") == "previous"
        assert ctec.get_terminal_specific("kitty", "tab_bar_min_tabs") == 2
        assert ctec.tabs.active_foreground.to_hex() == "#ffffff"
        assert ctec.tabs.active_background.to_hex() == "#000000"

    def test_kitty_parse_hidden_tabs(self):
        """Test Kitty parses tab_bar_style=hidden as visibility=NEVER."""
        config = """
tab_bar_style hidden
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.visibility.value == "never"

    def test_kitty_parse_panes(self):
        """Test Kitty parses pane settings."""
        config = """
inactive_text_alpha 0.7
active_border_color #00ff00
inactive_border_color #555555
window_border_width 1.5pt
focus_follows_mouse yes
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.7
        assert ctec.panes.focus_follows_mouse is True
        # Kitty-specific border settings are stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "active_border_color") == "#00ff00"
        assert ctec.get_terminal_specific("kitty", "inactive_border_color") == "#555555"
        assert ctec.get_terminal_specific("kitty", "window_border_width") == "1.5pt"

    def test_kitty_export_tabs(self):
        """Test Kitty exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarStyle,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                position=TabBarPosition.BOTTOM,
                style=TabBarStyle.POWERLINE,
            )
        )
        # Add Kitty-specific alignment via terminal_specific
        ctec.add_terminal_specific("kitty", "tab_bar_align", "center")
        output = KittyAdapter.export(ctec)
        assert "tab_bar_edge bottom" in output
        assert "tab_bar_style powerline" in output
        assert "tab_bar_align center" in output

    def test_wezterm_parse_tabs(self):
        """Test WezTerm parses tab settings."""
        config = """
local wezterm = require "wezterm"
local config = wezterm.config_builder()
config.enable_tab_bar = true
config.tab_bar_at_bottom = true
config.use_fancy_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.tab_max_width = 25
config.show_tab_index_in_tab_bar = true
return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.style.value == "fancy"
        assert ctec.tabs.auto_hide_single is True
        assert ctec.tabs.max_width == 25
        assert ctec.tabs.show_index is True

    def test_wezterm_parse_panes(self):
        """Test WezTerm parses pane settings."""
        config = """
local wezterm = require "wezterm"
local config = wezterm.config_builder()
config.inactive_pane_hsb = {
  saturation = 1.0,
  brightness = 0.7,
}
config.pane_focus_follows_mouse = true
config.colors = {
  split = "#444444",
}
return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.7
        assert ctec.panes.focus_follows_mouse is True
        assert ctec.panes.divider_color.to_hex() == "#444444"

    def test_wezterm_export_tabs(self):
        """Test WezTerm exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarStyle,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                position=TabBarPosition.BOTTOM,
                style=TabBarStyle.FANCY,
                auto_hide_single=True,
            )
        )
        output = WeztermAdapter.export(ctec)
        assert "config.tab_bar_at_bottom = true" in output
        assert "config.use_fancy_tab_bar = true" in output
        assert "config.hide_tab_bar_if_only_one_tab = true" in output

    def test_alacritty_warns_about_tabs(self):
        """Test Alacritty warns when tabs config is present."""
        from console_cowboy.ctec.schema import TabBarVisibility, TabConfig

        ctec = CTEC(tabs=TabConfig(visibility=TabBarVisibility.AUTO))
        AlacrittyAdapter.export(ctec)
        assert any("does not support native tabs" in w for w in ctec.warnings)

    def test_alacritty_warns_about_panes(self):
        """Test Alacritty warns when panes config is present."""
        from console_cowboy.ctec.schema import PaneConfig

        ctec = CTEC(panes=PaneConfig(inactive_dim_factor=0.8))
        AlacrittyAdapter.export(ctec)
        assert any("does not support native split panes" in w for w in ctec.warnings)

    def test_alacritty_warns_about_tab_keybindings(self):
        """Test Alacritty warns when tab keybindings are exported."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(action="new_tab", key="t", mods=["ctrl", "shift"]),
            ]
        )
        AlacrittyAdapter.export(ctec)
        assert any("tab/pane operations" in w.lower() for w in ctec.warnings)

    def test_cross_terminal_tab_conversion(self):
        """Test tab config converts between terminals."""
        # Parse Ghostty config with tabs
        ghostty_config = """
window-show-tab-bar = always
gtk-tabs-location = bottom
window-inherit-working-directory = true
"""
        ctec = GhosttyAdapter.parse("test", content=ghostty_config)

        # Export to Kitty
        kitty_output = KittyAdapter.export(ctec)
        assert "tab_bar_edge bottom" in kitty_output
        assert "tab_bar_min_tabs 1" in kitty_output  # ALWAYS = min_tabs 1

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert "config.tab_bar_at_bottom = true" in wezterm_output

    def test_cross_terminal_pane_conversion(self):
        """Test pane config converts between terminals."""
        # Parse Kitty config with panes
        kitty_config = """
inactive_text_alpha 0.7
active_border_color #00ff00
inactive_border_color #555555
window_border_width 1.5pt
focus_follows_mouse yes
"""
        ctec = KittyAdapter.parse("test", content=kitty_config)

        # Export to Ghostty
        ghostty_output = GhosttyAdapter.export(ctec)
        assert "unfocused-split-opacity = 0.7" in ghostty_output
        assert "focus-follows-mouse = true" in ghostty_output

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert "brightness = 0.7" in wezterm_output
        assert "config.pane_focus_follows_mouse = true" in wezterm_output

    def test_tab_config_roundtrip_ghostty(self):
        """Test tab config roundtrip through Ghostty."""
        from console_cowboy.ctec.schema import (
            NewTabPosition,
            TabBarPosition,
            TabBarVisibility,
            TabConfig,
        )

        original = CTEC(
            tabs=TabConfig(
                visibility=TabBarVisibility.AUTO,
                position=TabBarPosition.TOP,
                new_tab_position=NewTabPosition.END,
                inherit_working_directory=True,
            )
        )
        output = GhosttyAdapter.export(original)
        parsed = GhosttyAdapter.parse("test", content=output)

        assert parsed.tabs.visibility == original.tabs.visibility
        assert parsed.tabs.position == original.tabs.position
        assert parsed.tabs.new_tab_position == original.tabs.new_tab_position
        assert (
            parsed.tabs.inherit_working_directory
            == original.tabs.inherit_working_directory
        )

    def test_pane_config_roundtrip_kitty(self):
        """Test pane config roundtrip through Kitty."""
        from console_cowboy.ctec.schema import PaneConfig

        original = CTEC(
            panes=PaneConfig(
                inactive_dim_factor=0.75,
                focus_follows_mouse=True,
            )
        )
        # Add Kitty-specific border settings via terminal_specific
        original.add_terminal_specific("kitty", "window_border_width", "2.0pt")
        original.add_terminal_specific("kitty", "active_border_color", "#00ff00")
        original.add_terminal_specific("kitty", "inactive_border_color", "#646464")

        output = KittyAdapter.export(original)
        parsed = KittyAdapter.parse("test", content=output)

        # Check common pane settings
        assert parsed.panes.inactive_dim_factor == original.panes.inactive_dim_factor
        assert parsed.panes.focus_follows_mouse == original.panes.focus_follows_mouse
        # Check Kitty-specific settings round-trip via terminal_specific
        assert parsed.get_terminal_specific(
            "kitty", "window_border_width"
        ) == original.get_terminal_specific("kitty", "window_border_width")
        assert parsed.get_terminal_specific(
            "kitty", "active_border_color"
        ) == original.get_terminal_specific("kitty", "active_border_color")
        assert parsed.get_terminal_specific(
            "kitty", "inactive_border_color"
        ) == original.get_terminal_specific("kitty", "inactive_border_color")


class TestEnvironmentVariables:
    """Tests for environment variable and shell args support."""

    def test_ghostty_parse_env_variables(self):
        """Test Ghostty parses environment variables."""
        config = """
env = EDITOR=nvim
env = COLORTERM=truecolor
env = TERM_PROGRAM=ghostty
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.environment_variables is not None
        assert ctec.behavior.environment_variables["EDITOR"] == "nvim"
        assert ctec.behavior.environment_variables["COLORTERM"] == "truecolor"
        assert ctec.behavior.environment_variables["TERM_PROGRAM"] == "ghostty"

    def test_ghostty_export_env_variables(self):
        """Test Ghostty exports environment variables."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                environment_variables={"EDITOR": "vim", "SHELL": "/bin/zsh"}
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "env = EDITOR=vim" in output
        assert "env = SHELL=/bin/zsh" in output

    def test_ghostty_env_roundtrip(self):
        """Test environment variables survive Ghostty round-trip."""
        original_config = """
env = MY_VAR=test_value
env = ANOTHER=another_value
"""
        parsed = GhosttyAdapter.parse("test", content=original_config)
        exported = GhosttyAdapter.export(parsed)
        reparsed = GhosttyAdapter.parse("test", content=exported)

        assert reparsed.behavior.environment_variables["MY_VAR"] == "test_value"
        assert reparsed.behavior.environment_variables["ANOTHER"] == "another_value"

    def test_alacritty_parse_env_variables(self):
        """Test Alacritty parses env section."""
        config = """
[env]
EDITOR = "nvim"
COLORTERM = "truecolor"
"""
        ctec = AlacrittyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.environment_variables is not None
        assert ctec.behavior.environment_variables["EDITOR"] == "nvim"
        assert ctec.behavior.environment_variables["COLORTERM"] == "truecolor"

    def test_alacritty_parse_shell_args(self):
        """Test Alacritty parses shell.args."""
        config = """
[shell]
program = "/bin/zsh"
args = ["-l", "-i"]
"""
        ctec = AlacrittyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.shell == "/bin/zsh"
        assert ctec.behavior.shell_args == ["-l", "-i"]

    def test_alacritty_export_env_and_shell_args(self):
        """Test Alacritty exports env and shell.args."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                shell="/bin/zsh",
                shell_args=["-l"],
                environment_variables={"EDITOR": "vim"},
            )
        )
        output = AlacrittyAdapter.export(ctec)
        # Check as TOML output - uses modern [terminal.shell] location
        assert "[terminal.shell]" in output
        assert '"program"' in output or "program" in output
        assert '["-l"]' in output or '"-l"' in output
        assert "[env]" in output
        assert "EDITOR" in output
        assert "vim" in output

    def test_kitty_parse_env_variables(self):
        """Test Kitty parses env directive."""
        config = """
env EDITOR=nvim
env COLORTERM=truecolor
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.environment_variables is not None
        assert ctec.behavior.environment_variables["EDITOR"] == "nvim"
        assert ctec.behavior.environment_variables["COLORTERM"] == "truecolor"

    def test_kitty_export_env_variables(self):
        """Test Kitty exports environment variables."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                environment_variables={"EDITOR": "vim", "TERM": "xterm-256color"}
            )
        )
        output = KittyAdapter.export(ctec)
        assert "env EDITOR=vim" in output
        assert "env TERM=xterm-256color" in output

    def test_wezterm_parse_env_variables(self):
        """Test WezTerm parses set_environment_variables."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.set_environment_variables = {
  EDITOR = "nvim",
  COLORTERM = "truecolor",
}

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.environment_variables is not None
        assert ctec.behavior.environment_variables["EDITOR"] == "nvim"
        assert ctec.behavior.environment_variables["COLORTERM"] == "truecolor"

    def test_wezterm_parse_shell_args(self):
        """Test WezTerm parses default_prog args."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.default_prog = { "/bin/zsh", "-l", "-i" }

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.shell == "/bin/zsh"
        assert ctec.behavior.shell_args == ["-l", "-i"]

    def test_wezterm_export_env_and_shell_args(self):
        """Test WezTerm exports env and default_prog with args."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                shell="/bin/zsh",
                shell_args=["-l", "-i"],
                environment_variables={"EDITOR": "vim"},
            )
        )
        output = WeztermAdapter.export(ctec)
        assert 'config.default_prog = { "/bin/zsh", "-l", "-i" }' in output
        assert "config.set_environment_variables" in output
        assert 'EDITOR = "vim"' in output

    def test_cross_terminal_env_conversion(self):
        """Test environment variables convert between terminals."""
        # Start with Ghostty config
        ghostty_config = """
env = EDITOR=nvim
env = COLORTERM=truecolor
"""
        ctec = GhosttyAdapter.parse("test", content=ghostty_config)

        # Export to Alacritty
        alacritty_output = AlacrittyAdapter.export(ctec)
        assert "[env]" in alacritty_output

        # Export to Kitty
        kitty_output = KittyAdapter.export(ctec)
        assert "env EDITOR=nvim" in kitty_output

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert "set_environment_variables" in wezterm_output

    def test_shell_args_warning_for_unsupported_terminals(self):
        """Test that terminals without shell_args support emit warnings."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                shell="/bin/zsh",
                shell_args=["-l", "-i"],
            )
        )

        # Ghostty doesn't support shell_args, should warn
        GhosttyAdapter.export(ctec)
        assert any("shell argument" in w.lower() for w in ctec.warnings)

        # Reset warnings
        ctec.warnings.clear()

        # Kitty doesn't support shell_args, should warn
        KittyAdapter.export(ctec)
        assert any("shell argument" in w.lower() for w in ctec.warnings)

    def test_iterm2_env_key_validation(self):
        """Test that iTerm2 validates environment variable keys to prevent injection."""
        ctec = CTEC(
            behavior=BehaviorConfig(
                environment_variables={
                    "VALID_KEY": "value1",
                    "_ALSO_VALID": "value2",
                    "invalid-key": "value3",  # Hyphens not allowed
                    "123_INVALID": "value4",  # Can't start with number
                    "FOO; rm -rf /": "malicious",  # Injection attempt
                }
            )
        )
        output = ITerm2Adapter.export(ctec)

        # Valid keys should be exported
        assert "export VALID_KEY=" in output
        assert "export _ALSO_VALID=" in output

        # Invalid keys should be skipped with warnings
        assert "invalid-key" not in output
        assert "123_INVALID" not in output
        assert "rm -rf" not in output

        # Should have warnings about skipped keys
        assert any("invalid-key" in w for w in ctec.warnings)
        assert any("123_INVALID" in w for w in ctec.warnings)
        assert any("FOO; rm -rf /" in w for w in ctec.warnings)


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
        from console_cowboy.ctec.schema import QuickTerminalConfig, QuickTerminalPosition

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
        from console_cowboy.ctec.schema import WindowConfig

        ctec = CTEC(window=WindowConfig(decorations=True))
        output = GhosttyAdapter.export(ctec)
        # Should use 'auto' not 'true' for cross-platform compatibility
        assert "window-decoration = auto" in output
        assert "window-decoration = true" not in output

    def test_ghostty_export_window_decoration_disabled(self):
        """Test Ghostty exports 'none' for disabled decorations."""
        from console_cowboy.ctec.schema import WindowConfig

        ctec = CTEC(window=WindowConfig(decorations=False))
        output = GhosttyAdapter.export(ctec)
        assert "window-decoration = none" in output


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
        assert "mouse_map left click ungrabbed mouse_handle_click selection link prompt" in output
        assert "mouse_map ctrl+left click ungrabbed mouse_handle_click selection link" in output

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
        assert "mouse_map left click ungrabbed mouse_handle_click selection link prompt" in output
        assert "macos_option_as_alt yes" in output
        assert "url_color #0087ff" in output
