"""Tests for font registry and validation utilities."""

from console_cowboy.utils.font_registry import (
    FontInfo,
    FontRegistry,
    find_similar_fonts,
    font_exists,
    validate_font,
)


class TestFontInfo:
    """Tests for the FontInfo dataclass."""

    def test_basic_font_info(self):
        """Test creating a basic FontInfo."""
        info = FontInfo(family="JetBrains Mono")
        assert info.family == "JetBrains Mono"
        assert info.style == "Regular"
        assert info.weight == 400
        assert info.is_monospace is False

    def test_font_info_with_all_fields(self):
        """Test FontInfo with all fields populated."""
        info = FontInfo(
            family="JetBrains Mono",
            postscript_name="JetBrainsMono-Regular",
            style="Regular",
            weight=400,
            is_monospace=True,
        )
        assert info.family == "JetBrains Mono"
        assert info.postscript_name == "JetBrainsMono-Regular"
        assert info.is_monospace is True

    def test_nerd_font_detection(self):
        """Test Nerd Font variant detection."""
        nf_info = FontInfo(family="JetBrains Mono Nerd Font")
        assert nf_info.is_nerd_font is True

        nf_short = FontInfo(family="JetBrainsMono NF")
        assert nf_short.is_nerd_font is True

        regular = FontInfo(family="JetBrains Mono")
        assert regular.is_nerd_font is False


class TestFontRegistry:
    """Tests for the FontRegistry class."""

    def test_registry_creation(self):
        """Test that registry can be created."""
        registry = FontRegistry.create()
        assert isinstance(registry, FontRegistry)

    def test_normalize_name(self):
        """Test font name normalization."""
        registry = FontRegistry()
        # Spaces and dashes should be removed, lowercased
        assert registry._normalize_name("JetBrains Mono") == "jetbrainsmono"
        assert (
            registry._normalize_name("JetBrainsMono-Regular") == "jetbrainsmonoregular"
        )

    def test_similarity_score(self):
        """Test similarity scoring."""
        registry = FontRegistry()
        # Same name should have high score
        score = registry._similarity_score("jetbrainsmono", "jetbrainsmono")
        assert score == 1.0

        # Similar names should have moderate score
        score = registry._similarity_score("jetbrainsmono", "jetbrains")
        assert 0.3 < score < 1.0

        # Very different names should have low score
        score = registry._similarity_score("jetbrainsmono", "xyz")
        assert score < 0.3

    def test_add_font(self):
        """Test adding fonts to registry."""
        registry = FontRegistry()
        info = FontInfo(family="Test Font", style="Regular")
        registry._add_font(info)

        assert "Test Font Regular" in registry.fonts
        assert "testfont" in registry._family_index

    def test_font_exists_with_added_font(self):
        """Test font_exists with manually added font."""
        registry = FontRegistry()
        info = FontInfo(family="Test Font", style="Regular")
        registry._add_font(info)

        assert registry.font_exists("Test Font") is True
        assert registry.font_exists("Nonexistent Font") is False

    def test_get_font_info(self):
        """Test getting font info."""
        registry = FontRegistry()
        info = FontInfo(
            family="Test Font",
            postscript_name="TestFont-Regular",
            style="Regular",
        )
        registry._add_font(info)

        retrieved = registry.get_font_info("Test Font")
        assert retrieved is not None
        assert retrieved.family == "Test Font"

    def test_find_similar_fonts(self):
        """Test finding similar fonts."""
        registry = FontRegistry()
        # Add some test fonts
        registry._add_font(FontInfo(family="JetBrains Mono"))
        registry._add_font(FontInfo(family="JetBrains Mono Bold", style="Bold"))
        registry._add_font(FontInfo(family="Fira Code"))

        similar = registry.find_similar_fonts("JetBrains", limit=5)
        # Should find JetBrains variants
        assert len(similar) > 0
        assert any("JetBrains" in s for s in similar)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_font_exists_function(self):
        """Test the font_exists convenience function."""
        # This will use the system registry - just check it doesn't error
        result = font_exists("NonexistentFont12345")
        assert result is False

    def test_find_similar_fonts_function(self):
        """Test the find_similar_fonts convenience function."""
        # With a non-existent font, should return empty or system suggestions
        result = find_similar_fonts("NonexistentFont12345")
        assert isinstance(result, list)

    def test_validate_font_function(self):
        """Test the validate_font convenience function."""
        # Non-existent font
        exists, suggestion = validate_font("NonexistentFont12345")
        assert exists is False
        assert suggestion is not None
        assert "not found" in suggestion.lower()
