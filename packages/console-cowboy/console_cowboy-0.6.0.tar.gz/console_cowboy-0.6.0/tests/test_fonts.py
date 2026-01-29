"""Tests for font name conversion utilities."""

import sys
from unittest.mock import patch

from console_cowboy.utils.fonts import (
    _get_system_font_names,
    _postscript_to_friendly_heuristic,
    extract_weight_from_name,
    friendly_to_postscript,
    is_postscript_name,
    normalize_font_family,
    postscript_to_friendly,
)


class TestPostScriptToFriendly:
    """Tests for PostScript to friendly name conversion.

    All tests mock _get_system_font_names to ensure deterministic behavior
    regardless of which fonts are installed on the system.
    """

    def test_jetbrains_mono(self):
        """Test JetBrainsMono conversion - removes -Regular suffix and adds spaces."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMono-Regular")
            assert "-Regular" not in result
            assert " " in result  # Has spaces (friendly format)
            assert "Mono" in result

    def test_fira_code(self):
        """Test FiraCode conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert postscript_to_friendly("FiraCode-Retina") == "Fira Code"

    def test_sf_mono(self):
        """Test SFMono conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert postscript_to_friendly("SFMono-Regular") == "SF Mono"

    def test_menlo(self):
        """Test Menlo conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert postscript_to_friendly("Menlo-Regular") == "Menlo"

    def test_monaco(self):
        """Test Monaco conversion (no suffix)."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert postscript_to_friendly("Monaco") == "Monaco"

    def test_nerd_font(self):
        """Test Nerd Font suffix preservation."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMono-NF-Regular")
            assert "-Regular" not in result
            assert "NF" in result
            assert "Mono" in result

    def test_meslo(self):
        """Test MesloLGS conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("MesloLGS-NF-Regular")
            assert "Meslo" in result

    def test_bold_suffix(self):
        """Test Bold suffix removal."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMono-Bold")
            assert "-Bold" not in result
            assert "Mono" in result

    def test_italic_suffix(self):
        """Test Italic suffix removal."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMono-Italic")
            assert "-Italic" not in result
            assert "Mono" in result

    def test_empty_string(self):
        """Test empty string handling."""
        assert postscript_to_friendly("") == ""

    def test_none_handling(self):
        """Test None-like handling."""
        assert postscript_to_friendly(None) is None

    def test_abbreviated_reg_suffix(self):
        """Test -Reg abbreviated suffix removal."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("FiraCode-Reg")
            assert "-Reg" not in result
            assert "Fira Code" == result

    def test_nfp_suffix(self):
        """Test NFP (Nerd Font Patched) suffix handling."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMonoNFP")
            assert "NFP" in result
            assert " NFP" in result  # Should have space before NFP

    def test_m_plus_code_font(self):
        """Test M+Code font with + character preserved."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("M+CodeLat60NFP-Reg")
            assert "M+Code" in result  # + should be preserved
            assert "-Reg" not in result  # Weight suffix removed
            assert "NFP" in result

    def test_m_plus_code_simple(self):
        """Test simple M+Code font."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("M+Code-Regular")
            assert "M+Code" in result
            assert "-Regular" not in result

    def test_font_with_numbers(self):
        """Test font name with version numbers like Lat60."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("M+CodeLat60-Regular")
            assert "Lat60" in result  # Numbers should be preserved
            assert "-Regular" not in result


class TestFriendlyToPostScript:
    """Tests for friendly to PostScript name conversion.

    All tests mock _get_system_font_names to ensure deterministic behavior
    regardless of which fonts are installed on the system.
    """

    def test_jetbrains_mono(self):
        """Test JetBrains Mono conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert friendly_to_postscript("JetBrains Mono") == "JetBrainsMono-Regular"

    def test_fira_code(self):
        """Test Fira Code conversion."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert friendly_to_postscript("Fira Code") == "FiraCode-Regular"

    def test_with_bold_weight(self):
        """Test with Bold weight."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            assert (
                friendly_to_postscript("JetBrains Mono", "Bold") == "JetBrainsMono-Bold"
            )

    def test_empty_string(self):
        """Test empty string handling."""
        assert friendly_to_postscript("") == ""


class TestIsPostScriptName:
    """Tests for PostScript name detection."""

    def test_with_regular_suffix(self):
        """Test detection with -Regular suffix."""
        assert is_postscript_name("JetBrainsMono-Regular") is True

    def test_with_bold_suffix(self):
        """Test detection with -Bold suffix."""
        assert is_postscript_name("FiraCode-Bold") is True

    def test_with_camel_case(self):
        """Test detection with camelCase."""
        assert is_postscript_name("JetBrainsMono") is True

    def test_friendly_name(self):
        """Test friendly name is not detected as PostScript."""
        assert is_postscript_name("JetBrains Mono") is False

    def test_simple_name(self):
        """Test simple name without spaces."""
        assert is_postscript_name("Monaco") is False

    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_postscript_name("") is False

    def test_none(self):
        """Test None returns False."""
        assert is_postscript_name(None) is False

    def test_abbreviated_reg_suffix(self):
        """Test detection with -Reg abbreviated suffix."""
        assert is_postscript_name("FiraCode-Reg") is True

    def test_m_plus_code_font(self):
        """Test M+Code font detection."""
        assert is_postscript_name("M+CodeLat60NFP-Reg") is True


class TestExtractWeightFromName:
    """Tests for weight extraction from font names."""

    def test_postscript_bold(self):
        """Test PostScript format with Bold."""
        base, weight = extract_weight_from_name("JetBrainsMono-Bold")
        assert base == "JetBrainsMono"
        assert weight == "Bold"

    def test_postscript_regular(self):
        """Test PostScript format with Regular."""
        base, weight = extract_weight_from_name("FiraCode-Regular")
        assert base == "FiraCode"
        assert weight == "Regular"

    def test_friendly_bold(self):
        """Test friendly format with Bold."""
        base, weight = extract_weight_from_name("JetBrains Mono Bold")
        assert base == "JetBrains Mono"
        assert weight == "Bold"

    def test_no_weight(self):
        """Test font name without weight suffix."""
        base, weight = extract_weight_from_name("Fira Code")
        assert base == "Fira Code"
        assert weight is None

    def test_no_weight_postscript(self):
        """Test PostScript name without weight suffix."""
        base, weight = extract_weight_from_name("Monaco")
        assert base == "Monaco"
        assert weight is None

    def test_semibold(self):
        """Test SemiBold weight."""
        base, weight = extract_weight_from_name("JetBrainsMono-SemiBold")
        assert base == "JetBrainsMono"
        assert weight == "SemiBold"

    def test_empty_string(self):
        """Test empty string."""
        base, weight = extract_weight_from_name("")
        assert base == ""
        assert weight is None

    def test_abbreviated_reg_suffix(self):
        """Test abbreviated -Reg suffix extraction."""
        base, weight = extract_weight_from_name("M+CodeLat60NFP-Reg")
        assert base == "M+CodeLat60NFP"
        assert weight == "Reg"


class TestNormalizeFontFamily:
    """Tests for font family normalization.

    Tests that use postscript_to_friendly mock _get_system_font_names
    to ensure deterministic behavior.
    """

    def test_postscript_with_weight(self):
        """Test normalizing PostScript name with weight."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = normalize_font_family("JetBrainsMono-Bold")
            # Should remove weight and convert to friendly
            assert "-Bold" not in result
            assert " " in result or result == "JetBrainsMono"

    def test_friendly_name(self):
        """Test friendly name passes through."""
        result = normalize_font_family("JetBrains Mono")
        assert result == "JetBrains Mono"

    def test_friendly_with_weight(self):
        """Test friendly name with weight gets weight removed."""
        result = normalize_font_family("JetBrains Mono Bold")
        assert result == "JetBrains Mono"

    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_font_family("") == ""

    def test_none_handling(self):
        """Test None handling."""
        assert normalize_font_family(None) is None


class TestSystemFontLookup:
    """Tests for system font database lookups."""

    def test_heuristic_fallback_when_system_returns_none(self):
        """Test that heuristics are used when system lookup fails."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            # Should fall back to heuristics
            result = postscript_to_friendly("JetBrainsMono-Regular")
            assert "Mono" in result
            assert "-Regular" not in result

    def test_system_lookup_used_when_available(self):
        """Test that system lookup is preferred when available."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names",
            return_value=("System Font Name", "SystemFontName-Regular"),
        ):
            result = postscript_to_friendly("AnyFont")
            assert result == "System Font Name"

    def test_friendly_to_postscript_uses_system_lookup(self):
        """Test that friendly_to_postscript uses system lookup."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names",
            return_value=("System Font", "SystemFont-Regular"),
        ):
            result = friendly_to_postscript("System Font")
            assert result == "SystemFont-Regular"

    def test_friendly_to_postscript_respects_weight_override(self):
        """Test that weight override works with system lookup."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names",
            return_value=("System Font", "SystemFont-Regular"),
        ):
            result = friendly_to_postscript("System Font", "Bold")
            assert "Bold" in result
            assert "SystemFont" in result

    def test_heuristic_preserves_special_characters(self):
        """Test that heuristic handles fonts with + character."""
        # Direct test of heuristic function
        result = _postscript_to_friendly_heuristic("M+Code-Regular")
        assert "M+Code" in result
        assert "-Regular" not in result

    def test_get_system_font_names_unsupported_platform(self):
        """Test that unsupported platforms return None."""
        with patch.object(sys, "platform", "win32"):
            result = _get_system_font_names("AnyFont")
            assert result is None


class TestSystemFontLookupEdgeCases:
    """Tests for edge cases in system font lookup functions."""

    def test_fc_match_missing_returns_none(self):
        """Test that missing fc-match command returns None and falls back to heuristics."""

        with patch.object(sys, "platform", "linux"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run",
                side_effect=FileNotFoundError("fc-match not found"),
            ):
                from console_cowboy.utils.fonts import _get_font_names_linux

                result = _get_font_names_linux("JetBrainsMono-Regular")
                assert result is None

    def test_fc_match_returns_fallback_font_returns_none(self):
        """Test that fc-match returning a non-matching fallback font returns None."""
        import subprocess

        # Simulate fc-match returning DejaVu Sans Mono for a request for FiraCode
        mock_result = subprocess.CompletedProcess(
            args=["fc-match"],
            returncode=0,
            stdout="DejaVu Sans Mono\nDejaVuSansMono\n",
            stderr="",
        )
        with patch.object(sys, "platform", "linux"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run", return_value=mock_result
            ):
                from console_cowboy.utils.fonts import _get_font_names_linux

                result = _get_font_names_linux("FiraCode-Regular")
                # Should return None because DejaVu doesn't match FiraCode
                assert result is None

    def test_fc_match_returns_matching_font(self):
        """Test that fc-match returning a matching font returns the names."""
        import subprocess

        mock_result = subprocess.CompletedProcess(
            args=["fc-match"],
            returncode=0,
            stdout="Fira Code\nFiraCode-Regular\n",
            stderr="",
        )
        with patch.object(sys, "platform", "linux"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run", return_value=mock_result
            ):
                from console_cowboy.utils.fonts import _get_font_names_linux

                result = _get_font_names_linux("FiraCode-Regular")
                assert result == ("Fira Code", "FiraCode-Regular")

    def test_fc_match_timeout_returns_none(self):
        """Test that fc-match timeout returns None."""
        import subprocess

        with patch.object(sys, "platform", "linux"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="fc-match", timeout=2),
            ):
                from console_cowboy.utils.fonts import _get_font_names_linux

                result = _get_font_names_linux("AnyFont")
                assert result is None

    def test_osascript_missing_returns_none(self):
        """Test that missing osascript command (non-macOS) returns None."""
        with patch.object(sys, "platform", "darwin"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run",
                side_effect=FileNotFoundError("osascript not found"),
            ):
                from console_cowboy.utils.fonts import _get_font_names_macos

                result = _get_font_names_macos("JetBrainsMono-Regular")
                assert result is None

    def test_osascript_font_not_found_returns_none(self):
        """Test that osascript returning empty (font not found) returns None."""
        import subprocess

        # When NSFont can't find the font, the script returns empty string
        mock_result = subprocess.CompletedProcess(
            args=["osascript"], returncode=0, stdout="\n", stderr=""
        )
        with patch.object(sys, "platform", "darwin"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run", return_value=mock_result
            ):
                from console_cowboy.utils.fonts import _get_font_names_macos

                result = _get_font_names_macos("NonExistentFont-Regular")
                assert result is None

    def test_osascript_returns_font_names(self):
        """Test that osascript returning font names works correctly."""
        import subprocess

        mock_result = subprocess.CompletedProcess(
            args=["osascript"],
            returncode=0,
            stdout="JetBrains Mono|JetBrainsMono-Regular\n",
            stderr="",
        )
        with patch.object(sys, "platform", "darwin"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run", return_value=mock_result
            ):
                from console_cowboy.utils.fonts import _get_font_names_macos

                result = _get_font_names_macos("JetBrainsMono-Regular")
                assert result == ("JetBrains Mono", "JetBrainsMono-Regular")

    def test_osascript_timeout_returns_none(self):
        """Test that osascript timeout returns None."""
        import subprocess

        with patch.object(sys, "platform", "darwin"):
            with patch(
                "console_cowboy.utils.fonts.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=2),
            ):
                from console_cowboy.utils.fonts import _get_font_names_macos

                result = _get_font_names_macos("AnyFont")
                assert result is None

    def test_postscript_to_friendly_uses_heuristic_when_system_fails(self):
        """Test complete flow: system lookup fails, heuristic used."""
        # This tests the actual integration
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = postscript_to_friendly("JetBrainsMono-Regular")
            assert result == "JetBrains Mono"

    def test_friendly_to_postscript_uses_heuristic_when_system_fails(self):
        """Test complete flow: system lookup fails, heuristic used."""
        with patch(
            "console_cowboy.utils.fonts._get_system_font_names", return_value=None
        ):
            result = friendly_to_postscript("JetBrains Mono")
            assert result == "JetBrainsMono-Regular"
