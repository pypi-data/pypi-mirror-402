"""
CTEC Serializers - YAML and JSON serialization for CTEC configurations.

YAML is the primary format, aligning with the iTerm2-Color-Schemes ecosystem.
JSON is supported for programmatic use and editor validation via JSON Schema.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .schema import CTEC


class OutputFormat(Enum):
    """Supported output formats for CTEC serialization."""

    YAML = "yaml"
    JSON = "json"


# =============================================================================
# iTerm2-Color-Schemes YAML Format JSON Schema
# =============================================================================
# This is a standalone schema for terminal color schemes, designed to be
# compatible with the iTerm2-Color-Schemes project's YAML format.
# See: https://github.com/mbadolato/iTerm2-Color-Schemes
#
# This schema can be contributed upstream to iTerm2-Color-Schemes as a
# formal specification of their YAML format.
# =============================================================================

ITERM2_COLOR_SCHEME_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/zetlen/console-cowboy/iterm2-color-scheme.schema.json",
    "title": "Terminal Color Scheme",
    "description": (
        "Terminal color scheme format compatible with iTerm2-Color-Schemes YAML. "
        "See: https://github.com/mbadolato/iTerm2-Color-Schemes"
    ),
    "type": "object",
    "properties": {
        # Metadata (extended from Gogh format)
        "name": {
            "type": "string",
            "description": "Color scheme name",
        },
        "author": {
            "type": "string",
            "description": "Color scheme author",
        },
        "variant": {
            "type": "string",
            "enum": ["dark", "light"],
            "description": "Theme variant (dark or light)",
        },
        # Core semantic colors (Gogh base format)
        "foreground": {
            "$ref": "#/$defs/hexColor",
            "description": "Default text color",
        },
        "background": {
            "$ref": "#/$defs/hexColor",
            "description": "Default background color",
        },
        "cursor": {
            "$ref": "#/$defs/hexColor",
            "description": "Cursor color",
        },
        # Extended semantic colors (iTerm2-Color-Schemes additions)
        "cursor_text": {
            "$ref": "#/$defs/hexColor",
            "description": "Text color when under cursor (default: foreground)",
        },
        "selection": {
            "$ref": "#/$defs/hexColor",
            "description": "Selection highlight color (default: foreground)",
        },
        "selection_text": {
            "$ref": "#/$defs/hexColor",
            "description": "Selected text color (default: background)",
        },
        "bold": {
            "$ref": "#/$defs/hexColor",
            "description": "Bold text color (default: foreground)",
        },
        "link": {
            "$ref": "#/$defs/hexColor",
            "description": "Hyperlink/URL color",
        },
        "underline": {
            "$ref": "#/$defs/hexColor",
            "description": "Underlined text color",
        },
        "cursor_guide": {
            "$ref": "#/$defs/hexColor",
            "description": "Cursor guide/highlight color (default: cursor)",
        },
        # ANSI colors 0-7 (normal)
        "black": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 0 (normal black)",
        },
        "red": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 1 (normal red)",
        },
        "green": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 2 (normal green)",
        },
        "yellow": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 3 (normal yellow)",
        },
        "blue": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 4 (normal blue)",
        },
        "magenta": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 5 (normal magenta)",
        },
        "cyan": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 6 (normal cyan)",
        },
        "white": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 7 (normal white)",
        },
        # ANSI colors 8-15 (bright)
        "bright_black": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 8 (bright black)",
        },
        "bright_red": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 9 (bright red)",
        },
        "bright_green": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 10 (bright green)",
        },
        "bright_yellow": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 11 (bright yellow)",
        },
        "bright_blue": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 12 (bright blue)",
        },
        "bright_magenta": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 13 (bright magenta)",
        },
        "bright_cyan": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 14 (bright cyan)",
        },
        "bright_white": {
            "$ref": "#/$defs/hexColor",
            "description": "ANSI color 15 (bright white)",
        },
    },
    "additionalProperties": False,
    "$defs": {
        "hexColor": {
            "type": "string",
            "pattern": "^#[0-9a-fA-F]{6}$",
            "description": "Hex color string (e.g., '#ff0000')",
            "examples": ["#ffffff", "#000000", "#c5c8c6"],
        },
    },
}


# =============================================================================
# CTEC JSON Schema
# =============================================================================
# Full schema for CTEC (Common Terminal Emulator Configuration).
# References the iTerm2-Color-Scheme schema for the color_scheme field.
# =============================================================================

CTEC_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/zetlen/console-cowboy/ctec.schema.json",
    "title": "CTEC - Common Terminal Emulator Configuration",
    "description": "Portable terminal configuration format for cross-emulator settings migration",
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "description": "CTEC format version",
            "default": "1.0",
        },
        "source_terminal": {
            "type": "string",
            "description": "Terminal emulator this config was exported from",
            "enum": ["iterm2", "ghostty", "alacritty", "kitty", "wezterm"],
        },
        "color_scheme": {
            "$ref": "iterm2-color-scheme.schema.json",
            "description": "Color scheme (iTerm2-Color-Schemes YAML format)",
        },
        "font": {
            "type": "object",
            "description": "Font configuration",
            "properties": {
                "family": {"type": "string", "description": "Primary font family"},
                "size": {"type": "number", "description": "Font size in points"},
                "line_height": {
                    "type": "number",
                    "description": "Line height multiplier",
                },
                "cell_width": {
                    "type": "number",
                    "description": "Cell width multiplier",
                },
                "weight": {
                    "type": "string",
                    "description": "Font weight",
                    "enum": [
                        "thin",
                        "extralight",
                        "light",
                        "regular",
                        "medium",
                        "semibold",
                        "bold",
                        "extrabold",
                        "black",
                    ],
                },
                "style": {
                    "type": "string",
                    "enum": ["normal", "italic", "oblique"],
                },
                "bold_font": {"type": "string"},
                "italic_font": {"type": "string"},
                "bold_italic_font": {"type": "string"},
                "ligatures": {"type": "boolean"},
                "anti_aliasing": {"type": "boolean"},
                "fallback_fonts": {"type": "array", "items": {"type": "string"}},
                "symbol_map": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "draw_powerline_glyphs": {"type": "boolean"},
                "box_drawing_scale": {"type": "number"},
            },
            "additionalProperties": False,
        },
        "cursor": {
            "type": "object",
            "description": "Cursor configuration",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["block", "beam", "underline"],
                },
                "blink": {"type": "boolean"},
                "blink_interval": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
        "window": {
            "type": "object",
            "description": "Window configuration",
            "properties": {
                "columns": {"type": "integer", "minimum": 1},
                "rows": {"type": "integer", "minimum": 1},
                "opacity": {"type": "number", "minimum": 0, "maximum": 1},
                "blur": {"type": "integer", "minimum": 0},
                "padding_horizontal": {"type": "integer", "minimum": 0},
                "padding_vertical": {"type": "integer", "minimum": 0},
                "decorations": {"type": "boolean"},
                "startup_mode": {
                    "type": "string",
                    "enum": ["windowed", "maximized", "fullscreen"],
                },
                "dynamic_title": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "behavior": {
            "type": "object",
            "description": "Terminal behavior configuration",
            "properties": {
                "shell": {"type": "string"},
                "working_directory": {"type": "string"},
                "scrollback_lines": {"type": "integer", "minimum": 0},
                "mouse_enabled": {"type": "boolean"},
                "bell_mode": {"type": "string", "enum": ["none", "audible", "visual"]},
                "copy_on_select": {"type": "boolean"},
                "confirm_close": {"type": "boolean"},
                "close_on_exit": {
                    "type": "string",
                    "enum": ["close", "hold", "restart"],
                },
            },
            "additionalProperties": False,
        },
        "scroll": {
            "type": "object",
            "description": "Scrollback configuration",
            "properties": {
                "unlimited": {"type": "boolean"},
                "disabled": {"type": "boolean"},
                "lines": {"type": "integer", "minimum": 0},
                "multiplier": {"type": "number", "minimum": 0},
            },
            "additionalProperties": False,
        },
        "key_bindings": {
            "type": "array",
            "description": "Keyboard shortcuts",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "key": {"type": "string"},
                    "mods": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["action", "key"],
                "additionalProperties": False,
            },
        },
        "terminal_specific": {
            "type": "array",
            "description": "Terminal-specific settings that cannot be mapped",
            "items": {
                "type": "object",
                "properties": {
                    "terminal": {"type": "string"},
                    "key": {"type": "string"},
                    "value": {},
                },
                "required": ["terminal", "key", "value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["version"],
    "additionalProperties": False,
}


# Bundled version of CTEC schema with color_scheme inlined (for single-file use)
def _create_bundled_ctec_schema() -> dict[str, Any]:
    """Create a bundled CTEC schema with color_scheme inlined."""
    schema = json.loads(json.dumps(CTEC_JSON_SCHEMA))  # Deep copy
    # Replace $ref with inlined color_scheme schema
    color_scheme_schema = json.loads(json.dumps(ITERM2_COLOR_SCHEME_SCHEMA))
    # Remove standalone schema metadata
    del color_scheme_schema["$schema"]
    del color_scheme_schema["$id"]
    del color_scheme_schema["title"]
    color_scheme_schema["description"] = (
        "Color scheme (iTerm2-Color-Schemes YAML format). "
        "See: https://github.com/mbadolato/iTerm2-Color-Schemes"
    )
    # Move $defs to root level so $ref paths resolve correctly
    if "$defs" in color_scheme_schema:
        schema["$defs"] = color_scheme_schema["$defs"]
        del color_scheme_schema["$defs"]
    schema["properties"]["color_scheme"] = color_scheme_schema
    return schema


CTEC_JSON_SCHEMA_BUNDLED: dict[str, Any] = _create_bundled_ctec_schema()


class CTECSerializer:
    """
    Serializer for CTEC configurations.

    Supports reading and writing CTEC configs in YAML and JSON formats.
    YAML is the primary format, aligning with the iTerm2-Color-Schemes ecosystem.
    """

    @staticmethod
    def to_json(ctec: CTEC, indent: int = 2) -> str:
        """
        Serialize CTEC to JSON string.

        Args:
            ctec: The CTEC configuration to serialize
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(ctec.to_dict(), indent=indent)

    @staticmethod
    def to_yaml(ctec: CTEC) -> str:
        """
        Serialize CTEC to YAML string.

        Args:
            ctec: The CTEC configuration to serialize

        Returns:
            YAML string representation
        """
        return yaml.dump(ctec.to_dict(), default_flow_style=False, sort_keys=False)

    @staticmethod
    def serialize(ctec: CTEC, format: OutputFormat) -> str:
        """
        Serialize CTEC to the specified format.

        Args:
            ctec: The CTEC configuration to serialize
            format: Output format (YAML or JSON)

        Returns:
            String representation in the specified format
        """
        if format == OutputFormat.JSON:
            return CTECSerializer.to_json(ctec)
        elif format == OutputFormat.YAML:
            return CTECSerializer.to_yaml(ctec)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def from_json(content: str) -> CTEC:
        """
        Deserialize CTEC from JSON string.

        Args:
            content: JSON string

        Returns:
            CTEC configuration
        """
        data = json.loads(content)
        return CTEC.from_dict(data)

    @staticmethod
    def from_yaml(content: str) -> CTEC:
        """
        Deserialize CTEC from YAML string.

        Args:
            content: YAML string

        Returns:
            CTEC configuration
        """
        data = yaml.safe_load(content)
        return CTEC.from_dict(data)

    @staticmethod
    def deserialize(content: str, format: OutputFormat) -> CTEC:
        """
        Deserialize CTEC from the specified format.

        Args:
            content: String content to deserialize
            format: Input format (YAML or JSON)

        Returns:
            CTEC configuration
        """
        if format == OutputFormat.JSON:
            return CTECSerializer.from_json(content)
        elif format == OutputFormat.YAML:
            return CTECSerializer.from_yaml(content)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def detect_format(path: str | Path) -> OutputFormat:
        """
        Detect the format based on file extension.

        Args:
            path: Path to the file

        Returns:
            Detected output format

        Raises:
            ValueError: If the format cannot be determined
        """
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            return OutputFormat.JSON
        elif suffix in (".yaml", ".yml"):
            return OutputFormat.YAML
        else:
            raise ValueError(
                f"Cannot determine format from extension: {suffix}. "
                "Use --format to specify explicitly."
            )

    @staticmethod
    def read_file(path: str | Path, format: OutputFormat = None) -> CTEC:
        """
        Read CTEC from a file.

        Args:
            path: Path to the file
            format: Optional format override (auto-detected from extension if not provided)

        Returns:
            CTEC configuration
        """
        path = Path(path)
        if format is None:
            format = CTECSerializer.detect_format(path)
        content = path.read_text()
        return CTECSerializer.deserialize(content, format)

    @staticmethod
    def write_file(ctec: CTEC, path: str | Path, format: OutputFormat = None) -> None:
        """
        Write CTEC to a file.

        Args:
            ctec: The CTEC configuration to write
            path: Path to the output file
            format: Optional format override (auto-detected from extension if not provided)
        """
        path = Path(path)
        if format is None:
            format = CTECSerializer.detect_format(path)
        content = CTECSerializer.serialize(ctec, format)
        path.write_text(content)

    @staticmethod
    def get_json_schema(bundled: bool = True) -> dict[str, Any]:
        """
        Get the JSON Schema for CTEC format.

        Args:
            bundled: If True, returns schema with color_scheme inlined.
                     If False, returns schema with $ref to separate file.

        This schema can be used by editors for validation and autocompletion.
        Save it to a file and reference it in your YAML files:

            # yaml-language-server: $schema=./ctec.schema.json

        Returns:
            JSON Schema dictionary
        """
        return CTEC_JSON_SCHEMA_BUNDLED if bundled else CTEC_JSON_SCHEMA

    @staticmethod
    def get_color_scheme_schema() -> dict[str, Any]:
        """
        Get the standalone JSON Schema for terminal color schemes.

        This schema is compatible with the iTerm2-Color-Schemes YAML format
        and can be contributed upstream to their project.

        Returns:
            JSON Schema dictionary for color schemes
        """
        return ITERM2_COLOR_SCHEME_SCHEMA

    @staticmethod
    def write_json_schema(path: str | Path, bundled: bool = True) -> None:
        """
        Write the JSON Schema to a file.

        Args:
            path: Path to write the schema file
            bundled: If True, writes schema with color_scheme inlined
        """
        path = Path(path)
        schema = CTEC_JSON_SCHEMA_BUNDLED if bundled else CTEC_JSON_SCHEMA
        content = json.dumps(schema, indent=2)
        path.write_text(content)

    @staticmethod
    def write_color_scheme_schema(path: str | Path) -> None:
        """
        Write the standalone color scheme JSON Schema to a file.

        This is the schema that could be contributed to iTerm2-Color-Schemes.

        Args:
            path: Path to write the schema file
        """
        path = Path(path)
        content = json.dumps(ITERM2_COLOR_SCHEME_SCHEMA, indent=2)
        path.write_text(content)
