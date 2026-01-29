"""
CTEC - Common Terminal Emulator Configuration

A portable configuration format for terminal emulators that enables
migration of settings between different terminal applications.
"""

from .schema import (
    CTEC,
    BehaviorConfig,
    BellMode,
    Color,
    ColorScheme,
    ColorVariant,
    CursorConfig,
    CursorStyle,
    FontConfig,
    FontStyle,
    FontWeight,
    KeyBinding,
    QuickTerminalConfig,
    QuickTerminalPosition,
    QuickTerminalScreen,
    ScrollConfig,
    TerminalSpecificSetting,
    WindowConfig,
)
from .serializers import CTEC_JSON_SCHEMA, CTECSerializer, OutputFormat

__all__ = [
    "CTEC",
    "ColorScheme",
    "ColorVariant",
    "Color",
    "FontConfig",
    "FontWeight",
    "FontStyle",
    "CursorConfig",
    "CursorStyle",
    "WindowConfig",
    "BehaviorConfig",
    "BellMode",
    "ScrollConfig",
    "QuickTerminalConfig",
    "QuickTerminalPosition",
    "QuickTerminalScreen",
    "KeyBinding",
    "TerminalSpecificSetting",
    "CTECSerializer",
    "OutputFormat",
    "CTEC_JSON_SCHEMA",
]
