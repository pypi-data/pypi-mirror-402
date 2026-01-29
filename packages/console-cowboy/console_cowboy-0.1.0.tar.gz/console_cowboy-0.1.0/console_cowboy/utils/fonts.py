"""
Font name conversion utilities for terminal configurations.

Different terminal emulators use different font name formats:
- PostScript names: 'JetBrainsMono-Regular', 'FiraCode-Retina'
- Friendly/Display names: 'JetBrains Mono', 'Fira Code'

macOS/iTerm2 often stores fonts with PostScript names, while terminals
like Wezterm prefer friendly names.
"""

import re


def postscript_to_friendly(postscript_name: str) -> str:
    """
    Convert a PostScript font name to a friendly/display name.

    This uses heuristics to convert names like:
    - 'JetBrainsMono-Regular' -> 'JetBrains Mono'
    - 'FiraCode-Retina' -> 'Fira Code'
    - 'SFMono-Regular' -> 'SF Mono'
    - 'MesloLGS-NF-Regular' -> 'MesloLGS NF'

    Args:
        postscript_name: Font name in PostScript format

    Returns:
        Font name in friendly format
    """
    if not postscript_name:
        return postscript_name

    # Remove common weight/style suffixes
    name = postscript_name
    suffixes_to_remove = [
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
        "Regular",
        "Bold",
        "Italic",  # Without dash
    ]
    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break

    # Handle Nerd Font suffixes
    nerd_font_suffix = ""
    if "-NF" in name:
        nerd_font_suffix = " NF"
        name = name.replace("-NF", "")
    elif " Nerd Font" in name:
        # Already friendly format
        return postscript_name

    # Split on dashes first
    parts = name.split("-")
    friendly_parts = []

    for part in parts:
        # Insert spaces before uppercase letters (camelCase handling)
        # But be careful with acronyms like 'SF', 'LG', 'NF'
        spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", part)
        # Handle cases like 'SFMono' -> 'SF Mono'
        spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
        friendly_parts.append(spaced)

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

    This is a best-effort conversion:
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
    - End with weight suffixes like -Regular, -Bold

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
    - 'Fira Code' -> ('Fira Code', None)

    Args:
        font_name: Font name potentially containing weight

    Returns:
        Tuple of (base_name, weight) where weight may be None
    """
    if not font_name:
        return (font_name, None)

    # Common weight suffixes in order of specificity
    weights = [
        "ExtraBold",
        "SemiBold",
        "UltraBold",
        "DemiBold",
        "ExtraLight",
        "UltraLight",
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
