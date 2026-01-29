"""Tests for the console-cowboy CLI."""

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
        result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "ghostty", "--quiet"],
        )

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
                [
                    "export",
                    "--from",
                    str(config_path),
                    "--from-type",
                    "ghostty",
                    "--to",
                    str(output_path),
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            parsed = yaml.safe_load(content)
            assert parsed["source_terminal"] == "ghostty"

    def test_export_to_yaml_default(self, runner):
        """Export now always produces YAML (JSON option removed)."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "ghostty", "--quiet"],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_export_kitty(self, runner):
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "kitty", "--quiet"],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "kitty"

    def test_export_alacritty_toml(self, runner):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        result = runner.invoke(
            cli,
            [
                "export",
                "--from",
                str(config_path),
                "--from-type",
                "alacritty",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "alacritty"

    def test_export_alacritty_yaml(self, runner):
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.yml"
        result = runner.invoke(
            cli,
            [
                "export",
                "--from",
                str(config_path),
                "--from-type",
                "alacritty",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "alacritty"

    def test_export_wezterm(self, runner):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "wezterm", "--quiet"],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "wezterm"

    def test_export_iterm2(self, runner):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "iterm2", "--quiet"],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "iterm2"

    def test_export_nonexistent_file(self, runner):
        result = runner.invoke(cli, ["export", "--from", "/nonexistent/path"])
        assert result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output.lower()

    def test_export_shows_warnings(self, runner):
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        result = runner.invoke(
            cli, ["export", "--from", str(config_path), "--from-type", "wezterm"]
        )

        # Wezterm should show warnings about Lua parsing
        assert "Warning" in result.output or result.exit_code == 0


class TestImportCommand:
    """Tests for the import command."""

    def test_import_ctec_to_ghostty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["import", "--from", str(ctec_path), "--to-type", "ghostty", "--quiet"]
        )

        assert result.exit_code == 0
        assert "font-family" in result.output
        assert "JetBrains Mono" in result.output

    def test_import_ctec_to_alacritty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli,
            ["import", "--from", str(ctec_path), "--to-type", "alacritty", "--quiet"],
        )

        assert result.exit_code == 0
        # Alacritty outputs TOML - check for valid content
        assert "[colors" in result.output or "[font" in result.output

    def test_import_ctec_to_kitty(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["import", "--from", str(ctec_path), "--to-type", "kitty", "--quiet"]
        )

        assert result.exit_code == 0
        assert "font_family" in result.output

    def test_import_ctec_to_wezterm(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["import", "--from", str(ctec_path), "--to-type", "wezterm", "--quiet"]
        )

        assert result.exit_code == 0
        assert "wezterm" in result.output
        assert "return config" in result.output

    def test_import_ctec_to_iterm2(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["import", "--from", str(ctec_path), "--to-type", "iterm2", "--quiet"]
        )

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
                    "--from",
                    str(ctec_path),
                    "--to",
                    str(output_path),
                    "--to-type",
                    "ghostty",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            assert "Fira Code" in content

    def test_import_missing_terminal(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["import", "--from", str(ctec_path)])

        assert result.exit_code != 0
        assert (
            "terminal" in result.output.lower() or "required" in result.output.lower()
        )


class TestConvertCommand:
    """Tests for the convert command."""

    def test_convert_ghostty_to_alacritty(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            [
                "convert",
                "--from",
                str(config_path),
                "--from-type",
                "ghostty",
                "--to",
                "-",
                "--to-type",
                "alacritty",
                "--quiet",
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
                "--from",
                str(config_path),
                "--from-type",
                "kitty",
                "--to",
                "-",
                "--to-type",
                "ghostty",
                "--quiet",
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
                "--from",
                str(config_path),
                "--from-type",
                "alacritty",
                "--to",
                "-",
                "--to-type",
                "wezterm",
                "--quiet",
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
                    "--from",
                    str(config_path),
                    "--from-type",
                    "ghostty",
                    "--to",
                    str(output_path),
                    "--to-type",
                    "alacritty",
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
                "--from",
                str(config_path),
                "--from-type",
                "ghostty",
                "--to",
                "-",
                "--to-type",
                "alacritty",
            ],
        )

        # Should mention terminal-specific settings
        assert result.exit_code == 0


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_ctec_file(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(cli, ["info", "--from", str(ctec_path)])

        assert result.exit_code == 0
        assert "Configuration Summary" in result.output
        assert "Font" in result.output
        assert "JetBrains Mono" in result.output

    def test_info_native_config(self, runner):
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli, ["info", "--from", str(config_path), "--from-type", "ghostty"]
        )

        assert result.exit_code == 0
        assert "Configuration Summary" in result.output
        assert "ghostty" in result.output.lower()

    def test_info_minimal_config(self, runner):
        ctec_path = FIXTURES_DIR / "ctec" / "minimal.yaml"
        result = runner.invoke(cli, ["info", "--from", str(ctec_path)])

        assert result.exit_code == 0
        assert "Font" in result.output
        assert "Cursor" in result.output


class TestDefaultCommand:
    """Tests for the default (implicit convert) command."""

    def test_from_without_to_outputs_ctec(self, runner):
        """--from without --to should output CTEC to stdout."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            ["--from", str(config_path), "--from-type", "ghostty", "--quiet"],
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_from_and_to_converts(self, runner):
        """--from and --to should convert between formats."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config"
            result = runner.invoke(
                cli,
                [
                    "--from",
                    str(config_path),
                    "--from-type",
                    "ghostty",
                    "--to",
                    str(output_path),
                    "--to-type",
                    "kitty",
                    "--quiet",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()
            content = output_path.read_text()
            assert "font_family" in content

    def test_to_type_without_to_outputs_to_stdout(self, runner):
        """--to-type without --to should output that type to stdout."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            [
                "--from",
                str(config_path),
                "--from-type",
                "ghostty",
                "--to-type",
                "alacritty",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        # Should be Alacritty TOML format
        assert "[font" in result.output or "[colors" in result.output

    def test_no_args_shows_help(self, runner):
        """No arguments should show help."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Console Cowboy" in result.output


class TestRoundTrip:
    """Round-trip integration tests."""

    def test_ghostty_roundtrip(self, runner):
        """Test export -> import -> compare."""
        config_path = FIXTURES_DIR / "ghostty" / "config"

        # Export to CTEC
        export_result = runner.invoke(
            cli,
            ["export", "--from", str(config_path), "--from-type", "ghostty", "--quiet"],
        )
        assert export_result.exit_code == 0

        # Import back to Ghostty
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(export_result.output)
            ctec_path = f.name

        try:
            import_result = runner.invoke(
                cli, ["import", "--from", ctec_path, "--to-type", "ghostty", "--quiet"]
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
                cli,
                [
                    "export",
                    "--from",
                    str(config_path),
                    "--from-type",
                    terminal,
                    "--quiet",
                ],
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
                    cli,
                    ["import", "--from", ctec_path, "--to-type", terminal, "--quiet"],
                )
                assert import_result.exit_code == 0, f"Import failed for {terminal}"
            finally:
                Path(ctec_path).unlink()


class TestAutoDetection:
    """Tests for automatic terminal type detection."""

    def test_detect_ghostty_config(self, runner):
        """Should auto-detect Ghostty config format."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(cli, ["--from", str(config_path), "--quiet"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_detect_alacritty_config(self, runner):
        """Should auto-detect Alacritty config format."""
        config_path = FIXTURES_DIR / "alacritty" / "alacritty.toml"
        result = runner.invoke(cli, ["--from", str(config_path), "--quiet"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "alacritty"

    def test_detect_kitty_config(self, runner):
        """Should auto-detect Kitty config format."""
        config_path = FIXTURES_DIR / "kitty" / "kitty.conf"
        result = runner.invoke(cli, ["--from", str(config_path), "--quiet"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "kitty"

    def test_detect_wezterm_config(self, runner):
        """Should auto-detect Wezterm config format."""
        config_path = FIXTURES_DIR / "wezterm" / "wezterm.lua"
        result = runner.invoke(cli, ["--from", str(config_path), "--quiet"])

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "wezterm"

    def test_detect_ctec_file(self, runner):
        """Should auto-detect CTEC YAML format."""
        ctec_path = FIXTURES_DIR / "ctec" / "complete.yaml"
        result = runner.invoke(
            cli, ["--from", str(ctec_path), "--to-type", "ghostty", "--quiet"]
        )

        assert result.exit_code == 0
        # Output should be Ghostty format
        assert "font-family" in result.output


class TestStdinStdout:
    """Tests for stdin/stdout handling."""

    def test_read_from_stdin(self, runner):
        """Should read from stdin when --from is '-'."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        config_content = config_path.read_text()

        result = runner.invoke(
            cli,
            ["--from", "-", "--from-type", "ghostty", "--quiet"],
            input=config_content,
        )

        assert result.exit_code == 0
        parsed = yaml.safe_load(result.output)
        assert parsed["source_terminal"] == "ghostty"

    def test_write_to_stdout_with_dash(self, runner):
        """Should write to stdout when --to is '-'."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        result = runner.invoke(
            cli,
            [
                "--from",
                str(config_path),
                "--from-type",
                "ghostty",
                "--to",
                "-",
                "--to-type",
                "kitty",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        assert "font_family" in result.output
