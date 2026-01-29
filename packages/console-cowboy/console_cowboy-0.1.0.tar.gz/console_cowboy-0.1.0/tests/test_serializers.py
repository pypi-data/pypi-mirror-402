"""Tests for CTEC serializers (YAML, JSON)."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from console_cowboy.ctec.schema import (
    CTEC,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
)
from console_cowboy.ctec.serializers import (
    CTEC_JSON_SCHEMA,
    CTEC_JSON_SCHEMA_BUNDLED,
    ITERM2_COLOR_SCHEME_SCHEMA,
    CTECSerializer,
    OutputFormat,
)


@pytest.fixture
def sample_ctec():
    """Create a sample CTEC configuration for testing."""
    return CTEC(
        source_terminal="test",
        color_scheme=ColorScheme(
            foreground=Color(255, 255, 255),
            background=Color(0, 0, 0),
        ),
        font=FontConfig(family="JetBrains Mono", size=14.0),
        cursor=CursorConfig(style=CursorStyle.BLOCK, blink=True),
    )


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_format_values(self):
        assert OutputFormat.YAML.value == "yaml"
        assert OutputFormat.JSON.value == "json"

    def test_format_iteration(self):
        formats = list(OutputFormat)
        assert len(formats) == 2
        assert OutputFormat.YAML in formats
        assert OutputFormat.JSON in formats


class TestJSONSerialization:
    """Tests for JSON serialization."""

    def test_to_json(self, sample_ctec):
        output = CTECSerializer.to_json(sample_ctec)
        assert isinstance(output, str)

        # Parse the output and verify
        parsed = json.loads(output)
        assert parsed["version"] == "1.0"
        assert parsed["source_terminal"] == "test"
        assert parsed["font"]["family"] == "JetBrains Mono"

    def test_to_json_with_indent(self, sample_ctec):
        output = CTECSerializer.to_json(sample_ctec, indent=4)
        # Check that it's properly indented
        assert "    " in output

    def test_from_json(self):
        json_content = """
{
    "version": "1.0",
    "source_terminal": "alacritty",
    "font": {
        "family": "Monaco",
        "size": 13.0
    }
}
"""
        ctec = CTECSerializer.from_json(json_content)
        assert ctec.source_terminal == "alacritty"
        assert ctec.font.family == "Monaco"
        assert ctec.font.size == 13.0

    def test_json_roundtrip(self, sample_ctec):
        json_str = CTECSerializer.to_json(sample_ctec)
        restored = CTECSerializer.from_json(json_str)

        assert restored.source_terminal == sample_ctec.source_terminal
        assert restored.font.family == sample_ctec.font.family


class TestYAMLSerialization:
    """Tests for YAML serialization."""

    def test_to_yaml(self, sample_ctec):
        output = CTECSerializer.to_yaml(sample_ctec)
        assert isinstance(output, str)

        # Parse the output and verify
        parsed = yaml.safe_load(output)
        assert parsed["version"] == "1.0"
        assert parsed["source_terminal"] == "test"
        assert parsed["font"]["family"] == "JetBrains Mono"

    def test_from_yaml(self):
        yaml_content = """
version: "1.0"
source_terminal: ghostty
font:
  family: Fira Code
  size: 12.0
cursor:
  style: underline
  blink: true
"""
        ctec = CTECSerializer.from_yaml(yaml_content)
        assert ctec.source_terminal == "ghostty"
        assert ctec.font.family == "Fira Code"
        assert ctec.cursor.style == CursorStyle.UNDERLINE

    def test_yaml_roundtrip(self, sample_ctec):
        yaml_str = CTECSerializer.to_yaml(sample_ctec)
        restored = CTECSerializer.from_yaml(yaml_str)

        assert restored.source_terminal == sample_ctec.source_terminal
        assert restored.font.family == sample_ctec.font.family


class TestSerializeMethod:
    """Tests for the generic serialize method."""

    def test_serialize_json(self, sample_ctec):
        output = CTECSerializer.serialize(sample_ctec, OutputFormat.JSON)
        parsed = json.loads(output)
        assert parsed["version"] == "1.0"

    def test_serialize_yaml(self, sample_ctec):
        output = CTECSerializer.serialize(sample_ctec, OutputFormat.YAML)
        parsed = yaml.safe_load(output)
        assert parsed["version"] == "1.0"


class TestDeserializeMethod:
    """Tests for the generic deserialize method."""

    def test_deserialize_json(self):
        content = '{"version": "1.0", "font": {"family": "Test"}}'
        ctec = CTECSerializer.deserialize(content, OutputFormat.JSON)
        assert ctec.font.family == "Test"

    def test_deserialize_yaml(self):
        content = "version: '1.0'\nfont:\n  family: Test"
        ctec = CTECSerializer.deserialize(content, OutputFormat.YAML)
        assert ctec.font.family == "Test"


class TestFormatDetection:
    """Tests for format detection from file extension."""

    def test_detect_json(self):
        assert CTECSerializer.detect_format("config.json") == OutputFormat.JSON

    def test_detect_yaml(self):
        assert CTECSerializer.detect_format("config.yaml") == OutputFormat.YAML
        assert CTECSerializer.detect_format("config.yml") == OutputFormat.YAML

    def test_detect_unknown_raises(self):
        with pytest.raises(ValueError):
            CTECSerializer.detect_format("config.txt")

    def test_detect_toml_raises(self):
        # TOML is no longer supported
        with pytest.raises(ValueError):
            CTECSerializer.detect_format("config.toml")

    def test_detect_with_path_object(self):
        assert CTECSerializer.detect_format(Path("config.yaml")) == OutputFormat.YAML


class TestFileOperations:
    """Tests for file read/write operations."""

    def test_write_and_read_json(self, sample_ctec):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.json"
            CTECSerializer.write_file(sample_ctec, path)

            restored = CTECSerializer.read_file(path)
            assert restored.font.family == sample_ctec.font.family

    def test_write_and_read_yaml(self, sample_ctec):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            CTECSerializer.write_file(sample_ctec, path)

            restored = CTECSerializer.read_file(path)
            assert restored.font.family == sample_ctec.font.family

    def test_read_with_explicit_format(self, sample_ctec):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write as YAML but with .txt extension
            path = Path(tmpdir) / "config.txt"
            path.write_text(CTECSerializer.to_yaml(sample_ctec))

            # Read with explicit format
            restored = CTECSerializer.read_file(path, OutputFormat.YAML)
            assert restored.font.family == sample_ctec.font.family

    def test_write_with_explicit_format(self, sample_ctec):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write as JSON but with .txt extension
            path = Path(tmpdir) / "config.txt"
            CTECSerializer.write_file(sample_ctec, path, OutputFormat.JSON)

            # Verify it's valid JSON
            content = path.read_text()
            parsed = json.loads(content)
            assert parsed["font"]["family"] == sample_ctec.font.family


class TestJSONSchema:
    """Tests for JSON Schema generation."""

    def test_get_json_schema(self):
        schema = CTECSerializer.get_json_schema()
        assert "$schema" in schema
        assert schema["title"] == "CTEC - Common Terminal Emulator Configuration"
        assert "properties" in schema
        assert "color_scheme" in schema["properties"]

    def test_schema_has_color_scheme_properties(self):
        schema = CTECSerializer.get_json_schema()
        color_scheme = schema["properties"]["color_scheme"]["properties"]

        # Check for extended YAML fields
        assert "bold" in color_scheme
        assert "link" in color_scheme
        assert "underline" in color_scheme
        assert "cursor_guide" in color_scheme
        assert "variant" in color_scheme

    def test_write_json_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ctec.schema.json"
            CTECSerializer.write_json_schema(path)

            assert path.exists()
            content = json.loads(path.read_text())
            assert "$schema" in content

    def test_schema_bundled_constant_matches(self):
        """Test that get_json_schema(bundled=True) returns CTEC_JSON_SCHEMA_BUNDLED."""
        assert CTEC_JSON_SCHEMA_BUNDLED == CTECSerializer.get_json_schema(bundled=True)
        assert CTEC_JSON_SCHEMA_BUNDLED == CTECSerializer.get_json_schema()  # Default

    def test_schema_unbundled_constant_matches(self):
        """Test that get_json_schema(bundled=False) returns CTEC_JSON_SCHEMA."""
        assert CTEC_JSON_SCHEMA == CTECSerializer.get_json_schema(bundled=False)

    def test_get_color_scheme_schema(self):
        """Test getting the standalone color scheme schema."""
        schema = CTECSerializer.get_color_scheme_schema()
        assert schema == ITERM2_COLOR_SCHEME_SCHEMA
        assert "$schema" in schema
        assert schema["title"] == "Terminal Color Scheme"

    def test_color_scheme_schema_has_hex_colors(self):
        """Test that color scheme schema uses hex color format."""
        schema = ITERM2_COLOR_SCHEME_SCHEMA
        # Check hex color definition
        assert "$defs" in schema
        assert "hexColor" in schema["$defs"]
        assert schema["$defs"]["hexColor"]["pattern"] == "^#[0-9a-fA-F]{6}$"

    def test_write_color_scheme_schema(self):
        """Test writing the standalone color scheme schema to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "iterm2-color-scheme.schema.json"
            CTECSerializer.write_color_scheme_schema(path)

            assert path.exists()
            content = json.loads(path.read_text())
            assert "$schema" in content
            assert content["title"] == "Terminal Color Scheme"

    def test_bundled_schema_has_inlined_color_scheme(self):
        """Test that bundled schema has color_scheme properties inlined."""
        # Bundled should have properties directly
        assert "properties" in CTEC_JSON_SCHEMA_BUNDLED["properties"]["color_scheme"]
        # Should not have $ref
        assert "$ref" not in CTEC_JSON_SCHEMA_BUNDLED["properties"]["color_scheme"]

    def test_unbundled_schema_has_ref(self):
        """Test that unbundled schema uses $ref for color_scheme."""
        assert "$ref" in CTEC_JSON_SCHEMA["properties"]["color_scheme"]
        assert (
            CTEC_JSON_SCHEMA["properties"]["color_scheme"]["$ref"]
            == "iterm2-color-scheme.schema.json"
        )
