"""
Color conversion utilities for terminal configurations.

Different terminal emulators use different color representations:
- Hex strings: '#ff0000', 'ff0000'
- RGB tuples: (255, 0, 0)
- Float tuples: (1.0, 0.0, 0.0)
- Named colors: 'red', 'blue'

This module provides utilities for converting between these formats.
"""

from console_cowboy.ctec.schema import Color


def normalize_color(value: str | dict | tuple | list | Color) -> Color:
    """
    Normalize a color value from various formats to a Color object.

    Args:
        value: Color in various formats:
            - Hex string: '#ff0000' or 'ff0000'
            - Dict with r,g,b keys: {'r': 255, 'g': 0, 'b': 0}
            - Tuple/list of ints: (255, 0, 0) or [255, 0, 0]
            - Tuple/list of floats: (1.0, 0.0, 0.0)
            - Color object: passed through

    Returns:
        Color object

    Raises:
        ValueError: If the color format is not recognized
    """
    if isinstance(value, Color):
        return value

    if isinstance(value, str):
        return Color.from_hex(value)

    if isinstance(value, dict):
        if "r" in value and "g" in value and "b" in value:
            return Color(r=int(value["r"]), g=int(value["g"]), b=int(value["b"]))
        if "red" in value and "green" in value and "blue" in value:
            # Handle float values (0.0-1.0)
            r = value["red"]
            g = value["green"]
            b = value["blue"]
            if isinstance(r, float) and r <= 1.0:
                return Color(r=int(r * 255), g=int(g * 255), b=int(b * 255))
            return Color(r=int(r), g=int(g), b=int(b))
        raise ValueError(f"Dict must have r,g,b or red,green,blue keys: {value}")

    if isinstance(value, (tuple, list)):
        if len(value) < 3:
            raise ValueError(f"Color tuple must have at least 3 values: {value}")
        r, g, b = value[0], value[1], value[2]
        # Check if values are floats in 0-1 range
        if all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in (r, g, b)):
            return Color(r=int(r * 255), g=int(g * 255), b=int(b * 255))
        return Color(r=int(r), g=int(g), b=int(b))

    raise ValueError(f"Unsupported color format: {type(value)}")


def color_to_float_tuple(color: Color) -> tuple[float, float, float]:
    """
    Convert a Color to a tuple of floats (0.0-1.0).

    This is used by some terminal emulators like iTerm2.

    Args:
        color: Color object

    Returns:
        Tuple of (r, g, b) floats in range 0.0-1.0
    """
    return (color.r / 255.0, color.g / 255.0, color.b / 255.0)


def float_tuple_to_color(values: tuple[float, float, float]) -> Color:
    """
    Convert a tuple of floats (0.0-1.0) to a Color.

    Args:
        values: Tuple of (r, g, b) floats

    Returns:
        Color object
    """
    r, g, b = values
    return Color(r=int(r * 255), g=int(g * 255), b=int(b * 255))
