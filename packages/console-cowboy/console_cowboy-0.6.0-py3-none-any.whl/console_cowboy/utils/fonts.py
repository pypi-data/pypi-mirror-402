"""
Font name conversion utilities for terminal configurations.

Different terminal emulators use different font name formats:
- PostScript names: 'JetBrainsMono-Regular', 'FiraCode-Retina'
- Friendly/Display names: 'JetBrains Mono', 'Fira Code'

macOS/iTerm2 often stores fonts with PostScript names, while terminals
like Wezterm prefer friendly names.

This module uses system font APIs when available (Core Text on macOS,
fontconfig on Linux) to get authoritative font name mappings, falling
back to heuristics when the font isn't installed or on unsupported platforms.
"""

import re
import subprocess
import sys


def _get_system_font_names(font_name: str) -> tuple[str, str] | None:
    """
    Query the system font database for canonical font names.

    Args:
        font_name: Any font name (PostScript or friendly)

    Returns:
        Tuple of (friendly_name, postscript_name) or None if not found
    """
    if sys.platform == "darwin":
        return _get_font_names_macos(font_name)
    elif sys.platform.startswith("linux"):
        return _get_font_names_linux(font_name)
    return None


def _get_font_names_macos(font_name: str) -> tuple[str, str] | None:
    """Query NSFont for font names on macOS using JavaScript for Automation."""
    try:
        # Use JXA (JavaScript for Automation) to query NSFont
        # This avoids the need for pyobjc dependencies
        script = f"""
ObjC.import("AppKit");
const font = $.NSFont.fontWithNameSize("{font_name}", 12.0);
if (font.isNil()) {{
    "";
}} else {{
    const family = font.familyName.js;
    const ps = font.fontName.js;
    family + "|" + ps;
}}
"""
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("|")
            if len(parts) == 2:
                return (parts[0], parts[1])
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_font_names_linux(font_name: str) -> tuple[str, str] | None:
    """Query fontconfig for font names on Linux."""
    try:
        result = subprocess.run(
            ["fc-match", font_name, "--format=%{family}\n%{postscriptname}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) == 2 and lines[0] and lines[1]:
                family, postscript = lines[0], lines[1]
                # fc-match always returns a result (fallback font) even if
                # the requested font isn't installed. Verify the result
                # actually matches the query by checking if the query appears
                # in either the family or postscript name (case-insensitive).
                query_lower = font_name.lower().replace("-", "").replace(" ", "")
                family_lower = family.lower().replace(" ", "")
                postscript_lower = postscript.lower().replace("-", "")
                if (
                    query_lower.startswith(family_lower)
                    or family_lower.startswith(
                        query_lower.split("-")[0] if "-" in font_name else query_lower
                    )
                    or postscript_lower.startswith(
                        query_lower.split("-")[0] if "-" in font_name else query_lower
                    )
                ):
                    return (family, postscript)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def postscript_to_friendly(postscript_name: str) -> str:
    """
    Convert a PostScript font name to a friendly/display name.

    Tries system font database first (Core Text on macOS, fontconfig on Linux),
    then falls back to heuristics for uninstalled fonts or unsupported platforms.

    Examples:
    - 'JetBrainsMono-Regular' -> 'JetBrains Mono'
    - 'FiraCode-Retina' -> 'Fira Code'
    - 'SFMono-Regular' -> 'SF Mono'

    Args:
        postscript_name: Font name in PostScript format

    Returns:
        Font name in friendly format
    """
    if not postscript_name:
        return postscript_name

    # Try system lookup first
    system_names = _get_system_font_names(postscript_name)
    if system_names is not None:
        return system_names[0]  # friendly name

    # Fall back to heuristics
    return _postscript_to_friendly_heuristic(postscript_name)


def _postscript_to_friendly_heuristic(postscript_name: str) -> str:
    """
    Heuristic conversion from PostScript to friendly name.

    Used as fallback when font is not installed or on unsupported platforms.
    """
    # Remove common weight/style suffixes (including abbreviated forms)
    name = postscript_name
    suffixes_to_remove = [
        # Full suffixes with dash
        "-Regular",
        "-Bold",
        "-Italic",
        "-BoldItalic",
        "-Light",
        "-Medium",
        "-SemiBold",
        "-ExtraBold",
        "-Thin",
        "-Black",
        "-Heavy",
        "-Retina",
        "-Book",
        # Abbreviated suffixes with dash (common in some fonts)
        "-Reg",
        "-Med",
        "-Bld",
        "-Lt",
        "-It",
        "-Obl",
        # Suffixes without dash
        "Regular",
        "Bold",
        "Italic",
    ]
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break

    # Handle Nerd Font suffixes (NFP = Nerd Font Patched/Plus, NF = Nerd Font)
    nerd_font_suffix = ""
    if "-NF" in name:
        nerd_font_suffix = " NF"
        name = name.replace("-NF", "")
    elif name.endswith("NFP"):
        # NFP suffix (Nerd Font Patched) - common variant naming
        nerd_font_suffix = " NFP"
        name = name[:-3]
    elif name.endswith("NF") and len(name) > 2:
        # NF suffix without dash (e.g., "MesloLGSNF")
        # Only match if there's content before it
        nerd_font_suffix = " NF"
        name = name[:-2]
    elif " Nerd Font" in name:
        # Already friendly format
        return postscript_name

    # Known compound brand names that shouldn't be split internally
    # These are font foundry/brand names that look like camelCase but are single words
    compound_names = ["JetBrains", "DejaVu", "PowerLine"]

    def split_camelcase(s: str) -> str:
        """Split camelCase into separate words, preserving compound names."""
        result = s

        # Replace compound names with placeholders (all lowercase to avoid regex matches)
        placeholders = {}
        for i, compound in enumerate(compound_names):
            if compound in result:
                placeholder = f"xcompound{i}x"
                result = result.replace(compound, placeholder)
                placeholders[placeholder] = compound

        # Insert spaces before uppercase letters (camelCase handling)
        # But be careful with acronyms like 'SF', 'LG', 'NF'
        result = re.sub(r"([a-z])([A-Z])", r"\1 \2", result)
        # Handle cases like 'SFMono' -> 'SF Mono'
        result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", result)

        # Restore compound names
        for placeholder, compound in placeholders.items():
            result = result.replace(placeholder, compound)

        # Clean up multiple spaces
        return " ".join(result.split())

    # Split on dashes first
    parts = name.split("-")
    friendly_parts = []

    for part in parts:
        # Preserve + character in font names like "M+Code"
        # Split temporarily around + to process each segment
        if "+" in part:
            plus_segments = part.split("+")
            processed_segments = [split_camelcase(seg) for seg in plus_segments]
            friendly_parts.append("+".join(processed_segments))
        else:
            friendly_parts.append(split_camelcase(part))

    result = " ".join(friendly_parts)

    # Re-add Nerd Font suffix
    if nerd_font_suffix:
        result += nerd_font_suffix

    # Clean up any double spaces
    result = " ".join(result.split())

    return result


def friendly_to_postscript(friendly_name: str, weight: str = "Regular") -> str:
    """
    Convert a friendly font name to PostScript format.

    Tries system font database first (Core Text on macOS, fontconfig on Linux),
    then falls back to heuristics for uninstalled fonts or unsupported platforms.

    Examples:
    - 'JetBrains Mono' -> 'JetBrainsMono-Regular'
    - 'Fira Code' -> 'FiraCode-Regular'

    Args:
        friendly_name: Font name in friendly format
        weight: Font weight to append (default: 'Regular')

    Returns:
        Font name in PostScript format
    """
    if not friendly_name:
        return friendly_name

    # Try system lookup first
    system_names = _get_system_font_names(friendly_name)
    if system_names is not None:
        postscript = system_names[1]  # postscript name
        # System returns the actual PostScript name which may have a specific weight
        # If user requested a different weight, we need to substitute it
        if weight != "Regular":
            # Strip existing weight suffix and add requested one
            base, _ = extract_weight_from_name(postscript)
            postscript = f"{base}-{weight}"
        return postscript

    # Fall back to heuristics
    return _friendly_to_postscript_heuristic(friendly_name, weight)


def _friendly_to_postscript_heuristic(
    friendly_name: str, weight: str = "Regular"
) -> str:
    """
    Heuristic conversion from friendly name to PostScript.

    Used as fallback when font is not installed or on unsupported platforms.
    """
    # Remove spaces and join
    postscript = friendly_name.replace(" ", "")

    # Add weight suffix if not already present
    if weight and not any(
        postscript.endswith(w) for w in ["Regular", "Bold", "Italic"]
    ):
        postscript = f"{postscript}-{weight}"

    return postscript


def is_postscript_name(font_name: str) -> bool:
    """
    Heuristically determine if a font name is in PostScript format.

    PostScript names typically:
    - Have no spaces
    - Use CamelCase or have dashes
    - End with weight suffixes like -Regular, -Bold, -Reg

    Args:
        font_name: Font name to check

    Returns:
        True if the name appears to be PostScript format
    """
    if not font_name:
        return False

    # If it has spaces, it's likely a friendly name
    if " " in font_name:
        return False

    # Check for common PostScript patterns
    postscript_patterns = [
        # Full weight suffixes
        r"-Regular$",
        r"-Bold$",
        r"-Italic$",
        r"-Light$",
        r"-Medium$",
        r"-SemiBold$",
        r"-ExtraBold$",
        r"-Thin$",
        r"-Black$",
        r"-Retina$",
        r"-Book$",
        # Abbreviated weight suffixes
        r"-Reg$",
        r"-Med$",
        r"-Bld$",
        r"-Lt$",
        r"-It$",
        r"-Obl$",
        r"[a-z][A-Z]",  # CamelCase within word
    ]

    for pattern in postscript_patterns:
        if re.search(pattern, font_name):
            return True

    return False


def extract_weight_from_name(font_name: str) -> tuple[str, str | None]:
    """
    Extract weight/style suffix from a font name.

    Works with both PostScript and friendly names:
    - 'JetBrainsMono-Bold' -> ('JetBrainsMono', 'Bold')
    - 'JetBrains Mono Bold' -> ('JetBrains Mono', 'Bold')
    - 'M+CodeLat60NFP-Reg' -> ('M+CodeLat60NFP', 'Reg')
    - 'Fira Code' -> ('Fira Code', None)

    Args:
        font_name: Font name potentially containing weight

    Returns:
        Tuple of (base_name, weight) where weight may be None
    """
    if not font_name:
        return (font_name, None)

    # Common weight suffixes in order of specificity
    # Include both full and abbreviated forms
    weights = [
        "ExtraBold",
        "SemiBold",
        "UltraBold",
        "DemiBold",
        "ExtraLight",
        "UltraLight",
        "BoldItalic",
        "Bold",
        "Light",
        "Medium",
        "Regular",
        "Thin",
        "Black",
        "Heavy",
        "Italic",
        "Oblique",
        "Retina",
        "Book",
        # Abbreviated forms
        "Reg",
        "Med",
        "Bld",
        "Lt",
        "It",
        "Obl",
    ]

    # Check PostScript format (with dash)
    for weight in weights:
        if font_name.endswith(f"-{weight}"):
            return (font_name[: -len(weight) - 1], weight)

    # Check friendly format (with space)
    for weight in weights:
        if font_name.endswith(f" {weight}"):
            return (font_name[: -len(weight) - 1], weight)

    # Check no-separator format
    for weight in weights:
        if font_name.endswith(weight) and len(font_name) > len(weight):
            # Make sure we're not matching part of the font name
            base = font_name[: -len(weight)]
            if base and (base[-1].islower() or base[-1] == "-"):
                return (base.rstrip("-"), weight)

    return (font_name, None)


def normalize_font_family(font_name: str) -> str:
    """
    Normalize a font family name to a canonical form.

    Removes weight/style suffixes and converts to friendly format.

    Args:
        font_name: Font name in any format

    Returns:
        Normalized font family name
    """
    if not font_name:
        return font_name

    # Extract weight
    base_name, _ = extract_weight_from_name(font_name)

    # Convert to friendly if PostScript
    if is_postscript_name(base_name):
        return postscript_to_friendly(base_name)

    return base_name
