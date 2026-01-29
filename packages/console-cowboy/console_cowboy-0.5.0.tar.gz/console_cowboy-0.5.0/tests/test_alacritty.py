"""Tests for the Alacritty adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    CursorStyle,
    FontConfig,
    WindowConfig,
)
from console_cowboy.terminals import AlacrittyAdapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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

        ctec = CTEC(behavior=BehaviorConfig(shell="/bin/zsh"))
        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[terminal.shell]" in output or "terminal.shell" in output
        assert "program" in output
        assert "/bin/zsh" in output

    def test_export_yaml_uses_legacy_shell(self):
        """Export to YAML should use legacy [shell] location for backwards compatibility."""

        ctec = CTEC(behavior=BehaviorConfig(shell="/bin/zsh"))
        output = AlacrittyAdapter.export(ctec, use_toml=False)

        # YAML format should use legacy shell key
        assert "shell:" in output
        assert "program:" in output
        assert "/bin/zsh" in output
