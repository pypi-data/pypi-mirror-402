from typing import Any, Callable

from console_cowboy.ctec.schema import ColorScheme, CursorStyle
from console_cowboy.utils.colors import normalize_color


class CursorStyleMixin:
    """Mixin for handling cursor style conversions."""

    # Subclasses should define this map
    CURSOR_STYLE_MAP: dict[str | int, CursorStyle] = {}

    @classmethod
    def _get_cursor_style_reverse_map(cls) -> dict[CursorStyle, str | int]:
        """Lazy load reverse map."""
        if not hasattr(cls, "_cursor_style_reverse_map_cache"):
            cls._cursor_style_reverse_map_cache = {
                v: k for k, v in cls.CURSOR_STYLE_MAP.items()
            }
        return cls._cursor_style_reverse_map_cache

    @classmethod
    def get_cursor_style(
        cls, value: Any, default: CursorStyle = CursorStyle.BLOCK
    ) -> CursorStyle:
        """Get CursorStyle enum from terminal-specific value."""
        if isinstance(value, str):
            value = value.lower()
        return cls.CURSOR_STYLE_MAP.get(value, default)

    @classmethod
    def get_cursor_style_value(
        cls, style: CursorStyle, default: Any = "block"
    ) -> str | int:
        """Get terminal-specific value from CursorStyle enum."""
        return cls._get_cursor_style_reverse_map().get(style, default)


class ColorMapMixin:
    """Mixin for handling color mapping between terminal keys and CTEC."""

    # Subclasses should define this map: {terminal_key: ctec_key}
    COLOR_KEY_MAP: dict[str, str] = {}

    @classmethod
    def _get_color_key_reverse_map(cls) -> dict[str, str]:
        """Lazy load reverse map."""
        if not hasattr(cls, "_color_key_reverse_map_cache"):
            cls._color_key_reverse_map_cache = {
                v: k for k, v in cls.COLOR_KEY_MAP.items()
            }
        return cls._color_key_reverse_map_cache

    @classmethod
    def get_ctec_color_key(cls, terminal_key: str) -> str | None:
        """Get CTEC attribute name for a terminal color key."""
        return cls.COLOR_KEY_MAP.get(terminal_key)

    @classmethod
    def get_terminal_color_key(cls, ctec_key: str) -> str | None:
        """Get terminal key for a CTEC color attribute."""
        return cls._get_color_key_reverse_map().get(ctec_key)

    @classmethod
    def map_colors_to_ctec(
        cls,
        source_data: dict,
        scheme: ColorScheme,
        value_parser: Callable = normalize_color,
        on_error: Callable[[str, Any, Exception], None] | None = None,
    ) -> bool:
        """
        Map colors from a source dict to CTEC ColorScheme.

        Args:
            source_data: Dictionary containing terminal settings
            scheme: CTEC ColorScheme object to populate
            value_parser: Function to parse color value (default: normalize_color)
            on_error: Optional callback for parsing errors (key, value, exception)

        Returns:
            True if any color was successfully mapped
        """
        modified = False
        for term_key, ctec_key in cls.COLOR_KEY_MAP.items():
            if term_key in source_data:
                try:
                    color = value_parser(source_data[term_key])
                    setattr(scheme, ctec_key, color)
                    modified = True
                except (ValueError, TypeError) as e:
                    if on_error:
                        on_error(term_key, source_data[term_key], e)
        return modified

    @classmethod
    def map_ctec_to_colors(
        cls,
        scheme: ColorScheme,
        value_formatter: Callable = lambda c: c.to_hex(),
    ) -> dict[str, Any]:
        """
        Map CTEC ColorScheme to a dictionary of terminal specific keys.

        Args:
            scheme: CTEC ColorScheme object
            value_formatter: Function to format Color object (default: hex string)

        Returns:
            Dictionary of {terminal_key: formatted_color}
        """
        result = {}
        for ctec_key, term_key in cls._get_color_key_reverse_map().items():
            color = getattr(scheme, ctec_key, None)
            if color:
                result[term_key] = value_formatter(color)
        return result


class ParsingMixin:
    """Mixin for common parsing operations."""

    @classmethod
    def apply_line_mapping(
        cls,
        key: str,
        value: str,
        target_obj: Any,
        mapping: dict[str, tuple[str, Callable]],
        on_error: Callable[[str, str, Exception], None] | None = None,
    ) -> bool:
        """
        Apply a line-based key-value pair to a target object based on a mapping.

        Args:
            key: Config key (e.g., 'font-size')
            value: Config value string
            target_obj: Object to set attributes on (e.g., CTEC or FontConfig)
            mapping: Dict of {config_key: (target_attr, converter_func)}
            on_error: Callback for conversion errors

        Returns:
            True if the key was found in the mapping and processed.
        """
        if key not in mapping:
            return False

        target_attr, converter = mapping[key]
        try:
            converted_value = converter(value)
            setattr(target_obj, target_attr, converted_value)
            return True
        except (ValueError, TypeError) as e:
            if on_error:
                on_error(key, value, e)
            return True # Key matched, even if error occurred

    @classmethod
    def get_nested_value(cls, data: dict, path: str) -> Any:
        """Get a value from a nested dictionary using dot notation."""
        current = data
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @classmethod
    def apply_key_mapping(
        cls,
        source_data: dict,
        target_obj: Any,
        mapping: dict[str, tuple[str, Callable]],
        on_error: Callable[[str, Any, Exception], None] | None = None,
    ) -> bool:
        """
        Apply dictionary values to a target object based on a mapping.

        Args:
            source_data: Source dictionary
            target_obj: Object to set attributes on
            mapping: Dict of {source_path: (target_attr, converter)}
            on_error: Callback for conversion errors

        Returns:
            True if any value was successfully mapped
        """
        modified = False
        for source_path, (target_attr, converter) in mapping.items():
            value = cls.get_nested_value(source_data, source_path)
            if value is not None:
                try:
                    converted_value = converter(value)
                    setattr(target_obj, target_attr, converted_value)
                    modified = True
                except (ValueError, TypeError) as e:
                    if on_error:
                        on_error(source_path, value, e)
        return modified

