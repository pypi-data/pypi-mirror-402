"""
Validation utilities for CTEC configurations.

Provides font validation, availability checking, and user-friendly suggestions
when fonts are not found on the system.
"""

from dataclasses import dataclass, field

from .ctec.schema import CTEC, FontConfig
from .utils.font_registry import find_similar_fonts, validate_font


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)

    def add_font_suggestion(self, font: str, alternatives: list[str]) -> None:
        """Add font alternatives for a missing font."""
        self.suggestions[font] = alternatives

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        self.suggestions.update(other.suggestions)


def _extract_fonts_from_config(font: FontConfig, context: str) -> list[tuple[str, str]]:
    """Extract all font names from a FontConfig with their context."""
    fonts = []

    if font.family:
        fonts.append((font.family, f"{context}.family"))
    if font.bold_font:
        fonts.append((font.bold_font, f"{context}.bold_font"))
    if font.italic_font:
        fonts.append((font.italic_font, f"{context}.italic_font"))
    if font.bold_italic_font:
        fonts.append((font.bold_italic_font, f"{context}.bold_italic_font"))
    if font.fallback_fonts:
        for i, fb in enumerate(font.fallback_fonts):
            fonts.append((fb, f"{context}.fallback_fonts[{i}]"))

    return fonts


def validate_fonts(ctec: CTEC) -> ValidationResult:
    """
    Validate all fonts in a CTEC configuration.

    Checks:
    - Primary font family exists
    - Bold/italic fonts exist
    - Fallback fonts exist

    Args:
        ctec: CTEC configuration to validate

    Returns:
        ValidationResult with warnings for missing fonts and suggestions
    """
    result = ValidationResult()

    fonts_to_check: list[tuple[str, str]] = []

    # Font config
    if ctec.font:
        fonts_to_check.extend(_extract_fonts_from_config(ctec.font, "font"))

    # Validate each font
    for font_name, context in fonts_to_check:
        exists, suggestion = validate_font(font_name)
        if not exists:
            result.add_warning(f"Font '{font_name}' ({context}) not found on system")
            similar = find_similar_fonts(font_name)
            if similar:
                result.add_font_suggestion(font_name, similar)

    return result


def validate_ctec(ctec: CTEC, check_fonts: bool = True) -> ValidationResult:
    """
    Comprehensive validation of a CTEC configuration.

    Args:
        ctec: Configuration to validate
        check_fonts: Whether to check font availability (requires system access)

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult()

    # Add any existing warnings from CTEC
    result.warnings.extend(ctec.warnings)

    # Validate fonts if requested
    if check_fonts:
        font_result = validate_fonts(ctec)
        result.merge(font_result)

    # Validate scroll config consistency
    if ctec.scroll:
        if ctec.scroll.disabled and ctec.scroll.unlimited:
            result.add_warning(
                "Scroll config has both 'disabled' and 'unlimited' set; "
                "'disabled' takes precedence"
            )
        if ctec.scroll.disabled and ctec.scroll.lines:
            result.add_warning(
                "Scroll config has both 'disabled' and 'lines' set; "
                "'disabled' takes precedence"
            )

    # Validate font config consistency
    if ctec.font:
        if ctec.font.line_height is not None:
            if ctec.font.line_height < 0.5 or ctec.font.line_height > 3.0:
                result.add_warning(
                    f"Unusual line_height value: {ctec.font.line_height}. "
                    "Expected range is 0.5-3.0"
                )
        if ctec.font.cell_width is not None:
            if ctec.font.cell_width < 0.5 or ctec.font.cell_width > 3.0:
                result.add_warning(
                    f"Unusual cell_width value: {ctec.font.cell_width}. "
                    "Expected range is 0.5-3.0"
                )
        if ctec.font.size is not None:
            if ctec.font.size < 4 or ctec.font.size > 72:
                result.add_warning(
                    f"Unusual font size: {ctec.font.size}pt. Expected range is 4-72pt"
                )

    return result


def format_validation_result(result: ValidationResult) -> str:
    """
    Format a validation result for display.

    Args:
        result: ValidationResult to format

    Returns:
        Human-readable string representation
    """
    lines = []

    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error}")

    if result.warnings:
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")

    if result.suggestions:
        lines.append("\nFont suggestions:")
        for font, alternatives in result.suggestions.items():
            lines.append(f"  {font}: try {', '.join(alternatives)}")

    if not lines:
        lines.append("Validation passed with no issues.")

    return "\n".join(lines)
