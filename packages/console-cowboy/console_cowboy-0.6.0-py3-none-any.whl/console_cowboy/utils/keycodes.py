"""
Utilities for converting macOS virtual key codes and modifier flags.

macOS uses virtual key codes (integers) to represent physical keys, and
NSEventModifierFlags (bitmask) for modifier keys. This module provides
mappings to convert these to standard key names used by terminal emulators.

Reference:
- Virtual key codes: Carbon/Events.h kVK_* constants
- Modifier flags: Cocoa/NSEvent.h NSEventModifierFlags
"""

# macOS virtual key codes to key names
# Based on Carbon Events.h kVK_* constants
# Key names follow Ghostty/common terminal conventions
MACOS_KEYCODE_MAP: dict[int, str] = {
    # Letters (QWERTY layout)
    0: "a",
    1: "s",
    2: "d",
    3: "f",
    4: "h",
    5: "g",
    6: "z",
    7: "x",
    8: "c",
    9: "v",
    11: "b",
    12: "q",
    13: "w",
    14: "e",
    15: "r",
    16: "y",
    17: "t",
    18: "one",  # Number row
    19: "two",
    20: "three",
    21: "four",
    22: "six",
    23: "five",
    24: "equal",
    25: "nine",
    26: "seven",
    27: "minus",
    28: "eight",
    29: "zero",
    30: "right_bracket",
    31: "o",
    32: "u",
    33: "left_bracket",
    34: "i",
    35: "p",
    36: "Return",
    37: "l",
    38: "j",
    39: "apostrophe",
    40: "k",
    41: "semicolon",
    42: "backslash",
    43: "comma",
    44: "slash",
    45: "n",
    46: "m",
    47: "period",
    48: "Tab",
    49: "space",
    50: "grave",  # Backtick/grave accent
    51: "Backspace",
    53: "Escape",
    # Function keys
    96: "F5",
    97: "F6",
    98: "F7",
    99: "F3",
    100: "F8",
    101: "F9",
    103: "F11",
    105: "F13",
    107: "F14",
    109: "F10",
    111: "F12",
    113: "F15",
    118: "F4",
    119: "End",
    120: "F2",
    121: "Page_Down",
    122: "F1",
    123: "Left",
    124: "Right",
    125: "Down",
    126: "Up",
    115: "Home",
    116: "Page_Up",
    117: "Delete",  # Forward delete
    # Keypad
    65: "KP_Decimal",
    67: "KP_Multiply",
    69: "KP_Add",
    71: "KP_Clear",
    75: "KP_Divide",
    76: "KP_Enter",
    78: "KP_Subtract",
    81: "KP_Equal",
    82: "KP_0",
    83: "KP_1",
    84: "KP_2",
    85: "KP_3",
    86: "KP_4",
    87: "KP_5",
    88: "KP_6",
    89: "KP_7",
    91: "KP_8",
    92: "KP_9",
}

# macOS NSEventModifierFlags bitmask values
# Reference: NSEvent.h
MACOS_MODIFIER_CAPS_LOCK = 1 << 16  # 65536
MACOS_MODIFIER_SHIFT = 1 << 17  # 131072
MACOS_MODIFIER_CONTROL = 1 << 18  # 262144
MACOS_MODIFIER_OPTION = 1 << 19  # 524288 (Alt)
MACOS_MODIFIER_COMMAND = 1 << 20  # 1048576 (Super/Cmd)
MACOS_MODIFIER_FUNCTION = 1 << 23  # 8388608

# Mapping of modifier flags to standard modifier names
# Order matters: ctrl, shift, alt/opt, super/cmd is conventional
MACOS_MODIFIER_MAP: list[tuple[int, str]] = [
    (MACOS_MODIFIER_CONTROL, "ctrl"),
    (MACOS_MODIFIER_SHIFT, "shift"),
    (MACOS_MODIFIER_OPTION, "alt"),
    (MACOS_MODIFIER_COMMAND, "super"),
]


def keycode_to_name(keycode: int) -> str | None:
    """
    Convert a macOS virtual key code to a key name.

    Args:
        keycode: macOS virtual key code (e.g., 7 for 'x')

    Returns:
        Key name string (e.g., 'x', 'Return', 'F1') or None if unknown
    """
    return MACOS_KEYCODE_MAP.get(keycode)


def modifiers_to_list(modifier_flags: int | None) -> list[str]:
    """
    Convert macOS NSEventModifierFlags to a list of modifier names.

    Args:
        modifier_flags: Bitmask of modifier flags (e.g., 1441792), or None

    Returns:
        List of modifier names in conventional order (e.g., ['ctrl', 'shift', 'super'])
    """
    if modifier_flags is None:
        return []
    mods = []
    for flag, name in MACOS_MODIFIER_MAP:
        if modifier_flags & flag:
            mods.append(name)
    return mods


def macos_hotkey_to_keybind(
    key_code: int | None,
    modifier_flags: int | None,
    action: str = "toggle_quick_terminal",
    scope: str = "global",
) -> str | None:
    """
    Convert macOS hotkey (key code + modifiers) to a terminal keybind string.

    Args:
        key_code: macOS virtual key code
        modifier_flags: macOS NSEventModifierFlags bitmask
        action: Action name for the keybinding
        scope: Keybinding scope (e.g., 'global', 'application')

    Returns:
        Keybind string in Ghostty format (e.g., 'global:ctrl+shift+super+x=toggle_quick_terminal')
        or None if key_code is unknown
    """
    if key_code is None:
        return None

    key_name = keycode_to_name(key_code)
    if key_name is None:
        return None

    # Build modifier prefix
    mods = modifiers_to_list(modifier_flags or 0)

    # Build the key combination string
    if mods:
        key_combo = "+".join(mods + [key_name])
    else:
        key_combo = key_name

    # Build the full keybind string
    if scope and scope != "application":
        return f"{scope}:{key_combo}={action}"
    return f"{key_combo}={action}"
