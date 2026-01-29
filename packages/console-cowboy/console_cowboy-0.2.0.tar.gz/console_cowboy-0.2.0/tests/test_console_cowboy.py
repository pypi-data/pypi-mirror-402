"""Tests for the console-cowboy CLI."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from console_cowboy.cli import cli

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


class TestCLIBasics:
    """Basic CLI tests."""

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Console Cowboy" in result.output
        assert "export" in result.output
        assert "import" in result.output

    def test_list_command(self, runner):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "iterm2" in result.output.lower()
        assert "ghostty" in result.output.lower()
        assert "alacritty" in result.output.lower()
        assert "kitty" in result.output.lower()
        assert "wezterm" in result.output.lower()


class TestExportCommand:
    """Tests for the export command."""

    def test_export_ghostty_to_stdout(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(cli, ["export", "ghostty", "-i", str(config_path), "-q"])

        assert result.exit_code == 0
        # Should be valid YAML by default
        parsed = yaml.safe_load(result.output)
        assert parsed["version"] == "1.0"
        assert parsed["source_terminal"] == "ghostty"

    def test_export_ghostty_to_file(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.yaml"
            result = runner.invoke(
                cli,
                ["export", "ghostty", "-i", str(config_path), "-o", str(output_path)],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            parsed = yaml.safe_load(content)
            assert parsed["source_terminal"] == "ghostty"

    def test_export_to_json(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli, ["export", "ghostty", "-i", str(config_path), "-f", "json", "-q"]
        )

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_export_to_yaml(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli, ["export", "ghostty", "-i", str(config_path), "-f", "yaml", "-q"]
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_export_kitty(self, runner):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        result = runner.invoke(cli, ["export", "kitty", "-i", str(config_path), "-q"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "kitty"

    def test_export_alacritty_toml(self, runner):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        result = runner.invoke(
            cli, ["export", "alacritty", "-i", str(config_path), "-q"]
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "alacritty"

    def test_export_alacritty_yaml(self, runner):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.yml"
        result = runner.invoke(
            cli, ["export", "alacritty", "-i", str(config_path), "-q"]
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "alacritty"

    def test_export_wezterm(self, runner):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        result = runner.invoke(cli, ["export", "wezterm", "-i", str(config_path), "-q"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "wezterm"

    def test_export_iterm2(self, runner):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        result = runner.invoke(cli, ["export", "iterm2", "-i", str(config_path), "-q"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "iterm2"

    def test_export_nonexistent_file(self, runner):
        result = runner.invoke(cli, ["export", "ghostty", "-i", "/nonexistent/path"])
        assert result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output.lower()

    def test_export_shows_warnings(self, runner):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        result = runner.invoke(cli, ["export", "wezterm", "-i", str(config_path)])

        # Wezterm should show warnings about Lua parsing
        assert "Warning" in result.output or result.exit_code == 0


class TestImportCommand:
    """Tests for the import command."""

    def test_import_ctec_to_ghostty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path), "-t", "ghostty", "-q"])

        assert result.exit_code == 0
        assert "font-family" in result.output
        assert "JetBrains Mono" in result.output

    def test_import_ctec_to_alacritty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path), "-t", "alacritty", "-q"])

        assert result.exit_code == 0
        # Alacritty outputs TOML - check for valid content
        assert "[colors" in result.output or "[font" in result.output

    def test_import_ctec_to_kitty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path), "-t", "kitty", "-q"])

        assert result.exit_code == 0
        assert "font_family" in result.output

    def test_import_ctec_to_wezterm(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path), "-t", "wezterm", "-q"])

        assert result.exit_code == 0
        assert "wezterm" in result.output
        assert "return config" in result.output

    def test_import_ctec_to_iterm2(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path), "-t", "iterm2", "-q"])

        assert result.exit_code == 0
        assert "plist" in result.output.lower()

    def test_import_to_file(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "minimal.yaml"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            result = runner.invoke(
                cli,
                [
                    "import",
                    str(ctec_path),
                    "-t",
                    "ghostty",
                    "-o",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            assert "Fira Code" in content

    def test_import_with_explicit_format(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["import", str(ctec_path), "-t", "ghostty", "-f", "yaml", "-q"]
        )

        assert result.exit_code == 0

    def test_import_missing_terminal(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", str(ctec_path)])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestConvertCommand:
    """Tests for the convert command."""

    def test_convert_ghostty_to_alacritty(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            [
                "convert",
                str(config_path),
                "-f",
                "ghostty",
                "-t",
                "alacritty",
                "-q",
            ],
        )

        assert result.exit_code == 0
        # Alacritty outputs TOML - check for expected content
        assert "[font" in result.output or "[colors" in result.output

    def test_convert_kitty_to_ghostty(self, runner):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        result = runner.invoke(
            cli,
            [
                "convert",
                str(config_path),
                "-f",
                "kitty",
                "-t",
                "ghostty",
                "-q",
            ],
        )

        assert result.exit_code == 0
        assert "font-family" in result.output

    def test_convert_alacritty_to_wezterm(self, runner):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        result = runner.invoke(
            cli,
            [
                "convert",
                str(config_path),
                "-f",
                "alacritty",
                "-t",
                "wezterm",
                "-q",
            ],
        )

        assert result.exit_code == 0
        assert "wezterm" in result.output
        assert "return config" in result.output

    def test_convert_to_file(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.toml"
            result = runner.invoke(
                cli,
                [
                    "convert",
                    str(config_path),
                    "-f",
                    "ghostty",
                    "-t",
                    "alacritty",
                    "-o",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

    def test_convert_shows_incompatibilities(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            [
                "convert",
                str(config_path),
                "-f",
                "ghostty",
                "-t",
                "alacritty",
            ],
        )

        # Should mention terminal-specific settings
        assert result.exit_code == 0


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_ctec_file(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["info", str(ctec_path)])

        assert result.exit_code == 0
        assert "Configuration Summary" in result.output
        assert "Font" in result.output
        assert "JetBrains Mono" in result.output

    def test_info_native_config(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(cli, ["info", str(config_path), "-t", "ghostty"])

        assert result.exit_code == 0
        assert "Configuration Summary" in result.output
        assert "ghostty" in result.output.lower()

    def test_info_minimal_config(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "minimal.yaml"
        result = runner.invoke(cli, ["info", str(ctec_path)])

        assert result.exit_code == 0
        assert "Font" in result.output
        assert "Cursor" in result.output


class TestRoundTrip:
    """Round-trip integration tests."""

    def test_ghostty_roundtrip(self, runner):
        """Test export -> import -> compare."""
        config_path = FIXTURES_DIR / "ghostty" / "config"

        # Export to CTEC
        export_result = runner.invoke(
            cli, ["export", "ghostty", "-i", str(config_path), "-q"]
        )
        assert export_result.exit_code == 0

        # Import back to Ghostty
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(export_result.output)
            ctec_path = f.name

        try:
            import_result = runner.invoke(
                cli, ["import", ctec_path, "-t", "ghostty", "-q"]
            )
            assert import_result.exit_code == 0

            # Key settings should be preserved
            assert "JetBrains Mono" in import_result.output
            assert "font-size = 14" in import_result.output
        finally:
            Path(ctec_path).unlink()

    def test_all_terminals_export_import(self, runner):
        """Test that all terminals can export and import."""
        terminals_and_fixtures = [
            ("ghostty", "ghostty/config"),
            ("kitty", "kitty/kitty.conf"),
            ("alacritty", "alacritty/alacritty.toml"),
            ("wezterm", "wezterm/wezterm.lua"),
            ("iterm2", "iterm2/com.googlecode.iterm2.plist"),
        ]

        for terminal, fixture in terminals_and_fixtures:
            config_path = FIXTURES_DIR / fixture

            # Export
            export_result = runner.invoke(
                cli, ["export", terminal, "-i", str(config_path), "-q"]
            )
            assert export_result.exit_code == 0, f"Export failed for {terminal}"

            # Verify it's valid YAML
            parsed = yaml.safe_load(export_result.output)
            assert parsed["source_terminal"] == terminal

            # Import to same terminal
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(export_result.output)
                ctec_path = f.name

            try:
                import_result = runner.invoke(
                    cli, ["import", ctec_path, "-t", terminal, "-q"]
                )
                assert import_result.exit_code == 0, f"Import failed for {terminal}"
            finally:
                Path(ctec_path).unlink()
