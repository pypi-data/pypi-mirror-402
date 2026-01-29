"""Tests for environment variable and shell args support."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    ITerm2Adapter,
    KittyAdapter,
    WeztermAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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

    def test_mouse_hide_while_typing_ghostty(self):
        """Test mouse-hide-while-typing parsing and export in Ghostty."""
        config = "mouse-hide-while-typing = true"
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.mouse_hide_while_typing is True
        output = GhosttyAdapter.export(ctec)
        assert "mouse-hide-while-typing = true" in output

    def test_mouse_hide_while_typing_kitty(self):
        """Test mouse_hide_wait parsing and export in Kitty."""
        config = "mouse_hide_wait -1"
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.mouse_hide_while_typing is True
        output = KittyAdapter.export(ctec)
        assert "mouse_hide_wait -1" in output
        config2 = "mouse_hide_wait 3.0"
        ctec2 = KittyAdapter.parse("test", content=config2)
        assert ctec2.behavior is not None
        assert ctec2.behavior.mouse_hide_while_typing is False

    def test_mouse_hide_while_typing_wezterm(self):
        """Test hide_mouse_cursor_when_typing parsing and export in WezTerm."""
        config = """
local wezterm = require 'wezterm'
local config = {}
config.hide_mouse_cursor_when_typing = true
return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.mouse_hide_while_typing is True
        output = WeztermAdapter.export(ctec)
        assert "config.hide_mouse_cursor_when_typing = true" in output

    def test_mouse_hide_while_typing_roundtrip(self):
        """Test mouse_hide_while_typing survives roundtrip across terminals."""
        ghostty_config = "mouse-hide-while-typing = true"
        ctec = GhosttyAdapter.parse("test", content=ghostty_config)
        kitty_output = KittyAdapter.export(ctec)
        assert "mouse_hide_wait -1" in kitty_output
        wezterm_output = WeztermAdapter.export(ctec)
        assert "config.hide_mouse_cursor_when_typing = true" in wezterm_output


class TestTerminalTypeSupport:
    """Tests for terminal_type (TERM environment variable) support across terminals."""

    def test_ghostty_parse_terminal_type(self):
        """Test Ghostty parses term setting into terminal_type."""
        config = """
term = xterm-ghostty
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.terminal_type == "xterm-ghostty"

    def test_ghostty_export_terminal_type(self):
        """Test Ghostty exports terminal_type as term setting."""
        ctec = CTEC(behavior=BehaviorConfig(terminal_type="xterm-256color"))
        output = GhosttyAdapter.export(ctec)
        assert "term = xterm-256color" in output

    def test_ghostty_terminal_type_roundtrip(self):
        """Test terminal_type survives Ghostty round-trip."""
        config = """
term = xterm-ghostty
"""
        parsed = GhosttyAdapter.parse("test", content=config)
        exported = GhosttyAdapter.export(parsed)
        reparsed = GhosttyAdapter.parse("test", content=exported)
        assert reparsed.behavior.terminal_type == "xterm-ghostty"

    def test_kitty_parse_terminal_type(self):
        """Test Kitty parses term setting into terminal_type."""
        config = """
term xterm-kitty
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.terminal_type == "xterm-kitty"

    def test_kitty_export_terminal_type(self):
        """Test Kitty exports terminal_type as term setting."""
        ctec = CTEC(behavior=BehaviorConfig(terminal_type="xterm-256color"))
        output = KittyAdapter.export(ctec)
        assert "term xterm-256color" in output

    def test_kitty_terminal_type_roundtrip(self):
        """Test terminal_type survives Kitty round-trip."""
        config = """
term xterm-kitty
"""
        parsed = KittyAdapter.parse("test", content=config)
        exported = KittyAdapter.export(parsed)
        reparsed = KittyAdapter.parse("test", content=exported)
        assert reparsed.behavior.terminal_type == "xterm-kitty"

    def test_wezterm_parse_terminal_type(self):
        """Test WezTerm parses term setting into terminal_type."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.term = "xterm-256color"

return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.behavior is not None
        assert ctec.behavior.terminal_type == "xterm-256color"

    def test_wezterm_export_terminal_type(self):
        """Test WezTerm exports terminal_type as config.term."""
        ctec = CTEC(behavior=BehaviorConfig(terminal_type="wezterm"))
        output = WeztermAdapter.export(ctec)
        assert 'config.term = "wezterm"' in output

    def test_wezterm_terminal_type_roundtrip(self):
        """Test terminal_type survives WezTerm round-trip."""
        config = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.term = "xterm-256color"

return config
"""
        parsed = WeztermAdapter.parse("test", content=config)
        exported = WeztermAdapter.export(parsed)
        reparsed = WeztermAdapter.parse("test", content=exported)
        assert reparsed.behavior.terminal_type == "xterm-256color"

    def test_iterm2_parse_terminal_type(self):
        """Test iTerm2 parses Terminal Type setting into terminal_type."""
        import plistlib

        profile = {
            "Name": "Default",
            "Guid": "default",
            "Terminal Type": "xterm-256color",
        }
        plist_data = {"New Bookmarks": [profile]}
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test", content=content)
        assert ctec.behavior is not None
        assert ctec.behavior.terminal_type == "xterm-256color"

    def test_iterm2_export_terminal_type(self):
        """Test iTerm2 exports terminal_type as Terminal Type setting."""
        ctec = CTEC(behavior=BehaviorConfig(terminal_type="xterm-256color"))
        output = ITerm2Adapter.export(ctec)

        import plistlib

        data = plistlib.loads(output.encode())
        profile = data["New Bookmarks"][0]
        assert profile["Terminal Type"] == "xterm-256color"

    def test_iterm2_terminal_type_roundtrip(self):
        """Test terminal_type survives iTerm2 round-trip."""
        import plistlib

        profile = {
            "Name": "Default",
            "Guid": "default",
            "Terminal Type": "xterm-256color",
        }
        plist_data = {"New Bookmarks": [profile]}
        content = plistlib.dumps(plist_data).decode()

        parsed = ITerm2Adapter.parse("test", content=content)
        exported = ITerm2Adapter.export(parsed)
        reparsed = ITerm2Adapter.parse("test", content=exported)
        assert reparsed.behavior.terminal_type == "xterm-256color"

    def test_cross_terminal_terminal_type(self):
        """Test terminal_type converts correctly between terminals."""
        # Parse from Ghostty
        ghostty_config = """
term = xterm-256color
"""
        ctec = GhosttyAdapter.parse("test", content=ghostty_config)

        # Export to Kitty
        kitty_output = KittyAdapter.export(ctec)
        assert "term xterm-256color" in kitty_output

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert 'config.term = "xterm-256color"' in wezterm_output
