"""
JavaScript runtime support for parsing Hyper configuration files.

This module uses dukpy to embed a JavaScript interpreter and execute Hyper
config files with a mock module system that captures the exported configuration.
"""

from typing import Any

import dukpy  # type: ignore[import-untyped]


def execute_hyper_config(js_source: str) -> dict[str, Any]:
    """
    Execute a Hyper JavaScript config and return the captured configuration.

    The JavaScript environment is sandboxed to prevent arbitrary code execution.
    Only the module.exports pattern is supported.

    Args:
        js_source: The JavaScript source code to execute

    Returns:
        A dict containing the config values from module.exports

    Raises:
        ValueError: If the JavaScript code fails to execute or doesn't export config
    """
    # Wrap the user's code to capture module.exports
    # We create a mock module object and execute the user's code,
    # then return the exports
    # Note: Using a unique placeholder instead of %s to avoid issues with
    # user code containing printf-style format specifiers like %s, %d, etc.
    placeholder = "___HYPER_CONFIG_SOURCE___"
    wrapper = f"""
    (function() {{
        var module = {{ exports: {{}} }};
        var exports = module.exports;

        // User's code goes here
        {placeholder}

        return module.exports;
    }})()
    """

    try:
        result = dukpy.evaljs(wrapper.replace(placeholder, js_source))
    except Exception as e:
        raise ValueError(f"Failed to execute Hyper config: {e}") from e

    if result is None:
        raise ValueError("Hyper config did not export any configuration")

    if not isinstance(result, dict):
        raise ValueError(
            f"Hyper config must export an object, got {type(result).__name__}"
        )

    # Check if exports is actually empty (no config was assigned)
    if not result:
        raise ValueError("Hyper config did not export any configuration")

    return result


def parse_hyper_color(color_str: str) -> tuple[int, int, int] | None:
    """
    Parse a Hyper color string into RGB values.

    Supports:
    - Hex colors: #rgb, #rrggbb
    - rgba() colors: rgba(r, g, b, a)

    Args:
        color_str: The color string to parse

    Returns:
        Tuple of (r, g, b) values, or None if parsing fails
    """
    if not color_str:
        return None

    color_str = color_str.strip()

    # Handle hex colors
    if color_str.startswith("#"):
        hex_part = color_str[1:]
        if len(hex_part) == 3:
            # #rgb -> #rrggbb
            hex_part = "".join(c * 2 for c in hex_part)
        if len(hex_part) == 6:
            try:
                r = int(hex_part[0:2], 16)
                g = int(hex_part[2:4], 16)
                b = int(hex_part[4:6], 16)
                return (r, g, b)
            except ValueError:
                return None

    # Handle rgba() colors
    if color_str.startswith("rgba(") and color_str.endswith(")"):
        inner = color_str[5:-1]
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) >= 3:
            try:
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                return (r, g, b)
            except ValueError:
                return None

    # Handle rgb() colors
    if color_str.startswith("rgb(") and color_str.endswith(")"):
        inner = color_str[4:-1]
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) >= 3:
            try:
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                return (r, g, b)
            except ValueError:
                return None

    return None
