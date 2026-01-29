"""
Font registry for system font detection and validation.

Provides platform-specific font enumeration without heavy dependencies.
Uses:
- macOS: CoreText via PyObjC (optional) or fallback to fc-list
- Linux: fontconfig (fc-list command)
- Windows: Registry enumeration

If fonttools is available, provides enhanced font file analysis.
"""

import platform
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path


class FontFormat(Enum):
    """Font file formats."""

    TTF = "ttf"
    OTF = "otf"
    TTC = "ttc"
    WOFF = "woff"
    WOFF2 = "woff2"


@dataclass
class FontInfo:
    """Information about a system font."""

    family: str  # Friendly family name
    postscript_name: str | None = None  # PostScript name if available
    style: str = "Regular"  # Style variant (Regular, Bold, Italic, etc.)
    weight: int = 400  # Numeric weight (100-900)
    is_monospace: bool = False
    file_path: Path | None = None
    format: FontFormat | None = None

    @property
    def is_nerd_font(self) -> bool:
        """Check if this is a Nerd Font variant."""
        indicators = [" Nerd Font", " NF", "-NF"]
        return any(ind in self.family for ind in indicators)


@dataclass
class FontRegistry:
    """
    Registry of system fonts with lookup capabilities.

    Usage:
        registry = FontRegistry.create()

        # Check if font exists
        if registry.font_exists("JetBrains Mono"):
            print("Font found!")

        # Get font info
        info = registry.get_font_info("JetBrains Mono")

        # Find similar fonts when one doesn't exist
        similar = registry.find_similar_fonts("JetBrains Mono")
    """

    fonts: dict[str, FontInfo] = field(default_factory=dict)
    _family_index: dict[str, set[str]] = field(
        default_factory=dict
    )  # family -> set of full names
    _postscript_index: dict[str, str] = field(
        default_factory=dict
    )  # postscript -> family

    @classmethod
    def create(cls, refresh: bool = False) -> "FontRegistry":
        """Create and populate the font registry."""
        # Use cached version unless refresh requested
        return _get_cached_registry() if not refresh else cls._build_registry()

    @classmethod
    def _build_registry(cls) -> "FontRegistry":
        """Build registry from system fonts."""
        registry = cls()
        system = platform.system()

        if system == "Darwin":
            registry._enumerate_macos_fonts()
        elif system == "Linux":
            registry._enumerate_linux_fonts()
        elif system == "Windows":
            registry._enumerate_windows_fonts()

        return registry

    def font_exists(self, name: str) -> bool:
        """Check if a font exists on the system."""
        if not name:
            return False
        normalized = self._normalize_name(name)
        return (
            normalized in self._family_index
            or normalized in self._postscript_index
            or name in self.fonts
        )

    def get_font_info(self, name: str) -> FontInfo | None:
        """Get information about a font."""
        if not name:
            return None
        normalized = self._normalize_name(name)

        # Try direct lookup
        if name in self.fonts:
            return self.fonts[name]

        # Try family index
        if normalized in self._family_index:
            # Return the Regular variant if available
            for full_name in self._family_index[normalized]:
                if "Regular" in full_name or full_name == normalized:
                    return self.fonts.get(full_name)
            # Otherwise return first match
            return self.fonts.get(next(iter(self._family_index[normalized])))

        # Try PostScript index
        if normalized in self._postscript_index:
            family = self._postscript_index[normalized]
            return self.get_font_info(family)

        return None

    def find_similar_fonts(self, name: str, limit: int = 5) -> list[str]:
        """Find fonts similar to the given name."""
        if not name:
            return []
        # Strategy: fuzzy match on family names
        normalized = self._normalize_name(name)
        candidates = []

        for family in self._family_index.keys():
            score = self._similarity_score(normalized, family)
            if score > 0.3:  # Threshold for relevance
                candidates.append((self._get_display_name(family), score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        # Deduplicate
        seen = set()
        result = []
        for name, _ in candidates:
            if name not in seen:
                seen.add(name)
                result.append(name)
            if len(result) >= limit:
                break
        return result

    def get_monospace_fonts(self) -> list[str]:
        """Get all monospace fonts on the system."""
        return sorted(
            {info.family for info in self.fonts.values() if info.is_monospace}
        )

    def resolve_font_name(
        self, name: str, target_format: str = "friendly"
    ) -> str | None:
        """
        Resolve a font name to the requested format.

        Args:
            name: Font name in any format
            target_format: "friendly" or "postscript"

        Returns:
            Font name in requested format, or None if not found
        """
        info = self.get_font_info(name)
        if not info:
            return None

        if target_format == "postscript":
            return info.postscript_name or self._to_postscript(info.family)
        else:
            return info.family

    def _normalize_name(self, name: str) -> str:
        """Normalize font name for comparison."""
        return name.lower().replace(" ", "").replace("-", "")

    def _get_display_name(self, normalized: str) -> str:
        """Get a display name from the family index."""
        if normalized in self._family_index:
            # Get first match and extract family name
            for full_name in self._family_index[normalized]:
                if full_name in self.fonts:
                    return self.fonts[full_name].family
        return normalized

    def _to_postscript(self, friendly_name: str) -> str:
        """Convert a friendly name to PostScript format (best effort)."""
        # Remove spaces and add -Regular
        return friendly_name.replace(" ", "") + "-Regular"

    def _similarity_score(self, a: str, b: str) -> float:
        """Calculate similarity between two normalized names."""

        # Simple Jaccard similarity on character n-grams
        def ngrams(s: str, n: int = 3) -> set[str]:
            return {s[i : i + n] for i in range(len(s) - n + 1)}

        a_grams, b_grams = ngrams(a), ngrams(b)
        if not a_grams or not b_grams:
            return 0.0
        intersection = len(a_grams & b_grams)
        union = len(a_grams | b_grams)
        return intersection / union if union else 0.0

    def _enumerate_macos_fonts(self) -> None:
        """Enumerate fonts on macOS using CoreText or fc-list fallback."""
        try:
            # Try PyObjC/CoreText first (if available)
            self._enumerate_macos_coretext()
        except (ImportError, OSError):
            # Fallback to fc-list if installed
            self._enumerate_via_fc_list()

    def _enumerate_macos_coretext(self) -> None:
        """Enumerate fonts using CoreText (requires PyObjC)."""
        from CoreText import (
            CTFontCollectionCreateFromAvailableFonts,
            CTFontCollectionCreateMatchingFontDescriptors,
            CTFontDescriptorCopyAttribute,
            kCTFontFamilyNameAttribute,
            kCTFontNameAttribute,
            kCTFontStyleNameAttribute,
        )

        collection = CTFontCollectionCreateFromAvailableFonts(None)
        descriptors = CTFontCollectionCreateMatchingFontDescriptors(collection)

        if descriptors:
            for desc in descriptors:
                family = CTFontDescriptorCopyAttribute(desc, kCTFontFamilyNameAttribute)
                ps_name = CTFontDescriptorCopyAttribute(desc, kCTFontNameAttribute)
                style = (
                    CTFontDescriptorCopyAttribute(desc, kCTFontStyleNameAttribute)
                    or "Regular"
                )

                if family:
                    info = FontInfo(
                        family=str(family),
                        postscript_name=str(ps_name) if ps_name else None,
                        style=str(style),
                    )
                    self._add_font(info)

    def _enumerate_linux_fonts(self) -> None:
        """Enumerate fonts on Linux using fontconfig."""
        self._enumerate_via_fc_list()

    def _enumerate_via_fc_list(self) -> None:
        """Enumerate fonts using fc-list command."""
        try:
            result = subprocess.run(
                ["fc-list", "--format", "%{family}|%{postscriptname}|%{style}\\n"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 1:
                    family = parts[0].split(",")[0].strip()  # Take first family name
                    ps_name = parts[1] if len(parts) > 1 else None
                    style = parts[2] if len(parts) > 2 else "Regular"

                    if family:
                        info = FontInfo(
                            family=family,
                            postscript_name=ps_name if ps_name else None,
                            style=style.split(",")[0] if style else "Regular",
                        )
                        self._add_font(info)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # fc-list not available

    def _enumerate_windows_fonts(self) -> None:
        """Enumerate fonts on Windows using registry."""
        try:
            import winreg

            key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        # Name format is "Font Name (TrueType)" or similar
                        family = re.sub(r"\s*\([^)]+\)\s*$", "", name)
                        if family:
                            info = FontInfo(family=family)
                            self._add_font(info)
                        i += 1
                    except OSError:
                        break
        except (ImportError, OSError):
            pass

    def _add_font(self, info: FontInfo) -> None:
        """Add a font to the registry."""
        key = f"{info.family} {info.style}".strip()
        self.fonts[key] = info

        # Update indexes
        normalized = self._normalize_name(info.family)
        if normalized not in self._family_index:
            self._family_index[normalized] = set()
        self._family_index[normalized].add(key)

        if info.postscript_name:
            ps_normalized = self._normalize_name(info.postscript_name)
            self._postscript_index[ps_normalized] = info.family


@lru_cache(maxsize=1)
def _get_cached_registry() -> FontRegistry:
    """Get cached font registry."""
    return FontRegistry._build_registry()


# Convenience functions


def font_exists(name: str) -> bool:
    """Check if a font exists on the system."""
    return FontRegistry.create().font_exists(name)


def get_font_info(name: str) -> FontInfo | None:
    """Get information about a font."""
    return FontRegistry.create().get_font_info(name)


def find_similar_fonts(name: str, limit: int = 5) -> list[str]:
    """Find fonts similar to the given name."""
    return FontRegistry.create().find_similar_fonts(name, limit)


def validate_font(name: str) -> tuple[bool, str | None]:
    """
    Validate a font name and return suggestions if not found.

    Returns:
        Tuple of (exists, suggestion_message)
    """
    if font_exists(name):
        return (True, None)

    similar = find_similar_fonts(name)
    if similar:
        suggestion = f"Font '{name}' not found. Similar fonts: {', '.join(similar)}"
    else:
        suggestion = f"Font '{name}' not found on this system."

    return (False, suggestion)


def resolve_font_name(
    name: str,
    source_terminal: str | None = None,
    target_terminal: str | None = None,
) -> str:
    """
    Resolve a font name from source to target terminal format.

    Args:
        name: Font name in any format
        source_terminal: Terminal the name came from (for context)
        target_terminal: Terminal we're exporting to

    Returns:
        Font name in the appropriate format for target terminal
    """
    if not name:
        return name

    # Import here to avoid circular imports
    from .fonts import (
        friendly_to_postscript,
        is_postscript_name,
        postscript_to_friendly,
    )

    # Terminals that use PostScript names
    postscript_terminals = {"iterm2"}

    # Terminals that use friendly names
    friendly_terminals = {"ghostty", "alacritty", "kitty", "wezterm"}

    # Determine source format
    source_is_postscript = (
        source_terminal in postscript_terminals or is_postscript_name(name)
    )

    # Determine target format needed
    target_needs_postscript = target_terminal in postscript_terminals
    target_needs_friendly = target_terminal in friendly_terminals

    # Try system lookup first for accuracy
    registry = FontRegistry.create()
    resolved = registry.resolve_font_name(
        name, "postscript" if target_needs_postscript else "friendly"
    )
    if resolved:
        return resolved

    # Fallback to heuristic conversion
    if target_needs_postscript and not source_is_postscript:
        return friendly_to_postscript(name)
    elif target_needs_friendly and source_is_postscript:
        return postscript_to_friendly(name)

    return name
