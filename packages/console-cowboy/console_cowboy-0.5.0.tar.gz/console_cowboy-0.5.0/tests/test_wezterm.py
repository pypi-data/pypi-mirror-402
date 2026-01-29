"""Tests for the Wezterm adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
    KeyBinding,
    WindowConfig,
)
from console_cowboy.terminals import WeztermAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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

    def test_parse_window_frame(self):
        """Test WezTerm parses window_frame for fancy tab bar customization."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.window_frame = {
  font = wezterm.font { family = 'Roboto', weight = 'Bold' },
  font_size = 12.0,
  active_titlebar_bg = '#333333',
  inactive_titlebar_bg = '#444444',
}

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)

        # Should be stored in terminal_specific
        window_frame = None
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key == "window_frame":
                window_frame = setting.value
                break

        assert window_frame is not None
        assert window_frame.get("font_size") == 12.0
        assert window_frame.get("active_titlebar_bg") == "#333333"
        assert window_frame.get("inactive_titlebar_bg") == "#444444"

    def test_export_window_frame(self):
        """Test WezTerm exports window_frame from terminal_specific."""
        from console_cowboy.ctec.schema import TerminalSpecificSetting

        ctec = CTEC()
        ctec.terminal_specific.append(
            TerminalSpecificSetting(
                terminal="wezterm",
                key="window_frame",
                value={
                    "font_size": 14.0,
                    "active_titlebar_bg": "#222222",
                    "inactive_titlebar_bg": "#333333",
                },
            )
        )

        output = WeztermAdapter.export(ctec)
        assert "config.window_frame" in output
        assert "font_size = 14.0" in output
        assert 'active_titlebar_bg = "#222222"' in output
        assert 'inactive_titlebar_bg = "#333333"' in output

    def test_parse_ssh_domains(self):
        """Test WezTerm parses ssh_domains for multiplexer configuration."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.ssh_domains = {
  {
    name = 'production',
    remote_address = 'prod.example.com',
    username = 'deploy',
  },
  {
    name = 'staging',
    remote_address = 'staging.example.com',
    username = 'deploy',
  },
}

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)

        # Should be stored in terminal_specific
        ssh_domains = None
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key == "ssh_domains":
                ssh_domains = setting.value
                break

        assert ssh_domains is not None
        # The Lua parser returns a dict with numeric keys (1-indexed)
        assert len(ssh_domains) >= 2

    def test_parse_unix_domains(self):
        """Test WezTerm parses unix_domains for multiplexer configuration."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.unix_domains = {
  { name = 'unix' },
}

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)

        # Should be stored in terminal_specific
        unix_domains = None
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key == "unix_domains":
                unix_domains = setting.value
                break

        assert unix_domains is not None

    def test_parse_tls_clients(self):
        """Test WezTerm parses tls_clients for multiplexer configuration."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.tls_clients = {
  {
    name = 'secure-server',
    remote_address = 'server.example.com:8080',
    bootstrap_via_ssh = 'user@server.example.com',
  },
}

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)

        tls_clients = None
        for setting in ctec.get_terminal_specific("wezterm"):
            if setting.key == "tls_clients":
                tls_clients = setting.value
                break

        assert tls_clients is not None

    def test_export_ssh_domains(self):
        """Test WezTerm exports ssh_domains from terminal_specific."""
        from console_cowboy.ctec.schema import TerminalSpecificSetting

        ctec = CTEC()
        ctec.terminal_specific.append(
            TerminalSpecificSetting(
                terminal="wezterm",
                key="ssh_domains",
                value={
                    1: {
                        "name": "production",
                        "remote_address": "prod.example.com",
                        "username": "deploy",
                    },
                },
            )
        )

        output = WeztermAdapter.export(ctec)
        assert "config.ssh_domains" in output
        assert 'name = "production"' in output
        assert 'remote_address = "prod.example.com"' in output
        assert 'username = "deploy"' in output

    def test_export_ssh_domains_with_nested_options(self):
        """Test WezTerm exports ssh_domains with nested ssh_option table."""
        from console_cowboy.ctec.schema import TerminalSpecificSetting

        ctec = CTEC()
        ctec.terminal_specific.append(
            TerminalSpecificSetting(
                terminal="wezterm",
                key="ssh_domains",
                value={
                    1: {
                        "name": "production",
                        "remote_address": "prod.example.com",
                        "ssh_option": {
                            "identityfile": "/path/to/key",
                        },
                    },
                },
            )
        )

        output = WeztermAdapter.export(ctec)
        assert "config.ssh_domains" in output
        assert "ssh_option = {" in output
        assert 'identityfile = "/path/to/key"' in output

    def test_roundtrip_window_frame_and_domains(self):
        """Test WezTerm window_frame and domains survive round-trip."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.window_frame = {
  font_size = 11.0,
  active_titlebar_bg = '#111111',
}

config.ssh_domains = {
  {
    name = 'myserver',
    remote_address = 'server.example.com',
  },
}

config.unix_domains = {
  { name = 'unix' },
}

return config
"""
        # Parse
        ctec = WeztermAdapter.parse("test", content=config)

        # Export
        output = WeztermAdapter.export(ctec)

        # Verify window_frame is preserved
        assert "config.window_frame" in output
        assert "font_size = 11.0" in output
        assert 'active_titlebar_bg = "#111111"' in output

        # Verify ssh_domains is preserved
        assert "config.ssh_domains" in output
        assert 'name = "myserver"' in output

        # Verify unix_domains is preserved
        assert "config.unix_domains" in output

    def test_export_copy_on_select_warning(self):
        """Test WezTerm adds warning when exporting copy_on_select."""
        ctec = CTEC(behavior=BehaviorConfig(copy_on_select=True))
        WeztermAdapter.export(ctec)

        # Should have a warning about copy_on_select not being directly supported
        copy_warnings = [w for w in ctec.warnings if "copy_on_select" in w.lower()]
        assert len(copy_warnings) == 1
        assert "mouse_bindings" in copy_warnings[0]
