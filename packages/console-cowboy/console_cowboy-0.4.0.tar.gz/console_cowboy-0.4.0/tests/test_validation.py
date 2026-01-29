"""Tests for CTEC validation utilities."""

from console_cowboy.ctec.schema import (
    CTEC,
    FontConfig,
    ScrollConfig,
)
from console_cowboy.validation import (
    ValidationResult,
    format_validation_result,
    validate_ctec,
    validate_fonts,
)


class TestValidationResult:
    """Tests for the ValidationResult class."""

    def test_empty_result(self):
        """Test empty validation result."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.has_warnings is False
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.is_valid is True
        assert result.has_warnings is True
        assert "Test warning" in result.warnings

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_font_suggestion(self):
        """Test adding font suggestions."""
        result = ValidationResult()
        result.add_font_suggestion("Missing Font", ["Alt1", "Alt2"])
        assert "Missing Font" in result.suggestions
        assert result.suggestions["Missing Font"] == ["Alt1", "Alt2"]

    def test_merge(self):
        """Test merging validation results."""
        result1 = ValidationResult()
        result1.add_warning("Warning 1")
        result1.add_font_suggestion("Font1", ["Alt1"])

        result2 = ValidationResult()
        result2.add_warning("Warning 2")
        result2.add_error("Error 1")

        result1.merge(result2)
        assert len(result1.warnings) == 2
        assert len(result1.errors) == 1
        assert result1.is_valid is False


class TestValidateFonts:
    """Tests for font validation."""

    def test_no_fonts(self):
        """Test validation with no fonts configured."""
        ctec = CTEC()
        result = validate_fonts(ctec)
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_missing_font_warning(self):
        """Test that missing fonts generate warnings."""
        ctec = CTEC(font=FontConfig(family="NonexistentFont12345"))
        result = validate_fonts(ctec)
        # Should have a warning about the missing font
        assert result.has_warnings is True
        assert any("NonexistentFont12345" in w for w in result.warnings)


class TestValidateCTEC:
    """Tests for comprehensive CTEC validation."""

    def test_empty_ctec(self):
        """Test validation of empty CTEC."""
        ctec = CTEC()
        result = validate_ctec(ctec, check_fonts=False)
        assert result.is_valid is True

    def test_scroll_config_conflicting_flags(self):
        """Test warning for conflicting scroll config."""
        ctec = CTEC(scroll=ScrollConfig(disabled=True, unlimited=True))
        result = validate_ctec(ctec, check_fonts=False)
        assert result.has_warnings is True
        assert any(
            "disabled" in w.lower() and "unlimited" in w.lower()
            for w in result.warnings
        )

    def test_unusual_font_size_warning(self):
        """Test warning for unusual font size."""
        ctec = CTEC(
            font=FontConfig(size=2.0)  # Very small
        )
        result = validate_ctec(ctec, check_fonts=False)
        assert result.has_warnings is True
        assert any("font size" in w.lower() for w in result.warnings)

    def test_unusual_line_height_warning(self):
        """Test warning for unusual line height."""
        ctec = CTEC(
            font=FontConfig(line_height=5.0)  # Very large
        )
        result = validate_ctec(ctec, check_fonts=False)
        assert result.has_warnings is True
        assert any("line_height" in w.lower() for w in result.warnings)

    def test_ctec_warnings_included(self):
        """Test that CTEC warnings are included in result."""
        ctec = CTEC()
        ctec.add_warning("Existing warning")
        result = validate_ctec(ctec, check_fonts=False)
        assert "Existing warning" in result.warnings


class TestFormatValidationResult:
    """Tests for validation result formatting."""

    def test_format_empty(self):
        """Test formatting empty result."""
        result = ValidationResult()
        output = format_validation_result(result)
        assert "passed" in output.lower() or "no issues" in output.lower()

    def test_format_with_warnings(self):
        """Test formatting result with warnings."""
        result = ValidationResult()
        result.add_warning("Test warning message")
        output = format_validation_result(result)
        assert "Warning" in output
        assert "Test warning message" in output

    def test_format_with_suggestions(self):
        """Test formatting result with font suggestions."""
        result = ValidationResult()
        result.add_warning("Font 'Missing' not found")
        result.add_font_suggestion("Missing", ["Alt1", "Alt2"])
        output = format_validation_result(result)
        assert "suggestion" in output.lower()
        assert "Alt1" in output
