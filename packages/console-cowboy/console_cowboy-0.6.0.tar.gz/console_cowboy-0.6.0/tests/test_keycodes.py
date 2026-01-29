"""Tests for macOS key code and modifier conversion utilities."""


class TestMacOSKeyCodeConversion:
    """Tests for macOS key code and modifier conversion utilities."""

    def test_keycode_to_name_letters(self):
        """Test conversion of letter key codes."""
        from console_cowboy.utils.keycodes import keycode_to_name

        assert keycode_to_name(0) == "a"
        assert keycode_to_name(7) == "x"
        assert keycode_to_name(12) == "q"
        assert keycode_to_name(35) == "p"

    def test_keycode_to_name_special_keys(self):
        """Test conversion of special key codes."""
        from console_cowboy.utils.keycodes import keycode_to_name

        assert keycode_to_name(36) == "Return"
        assert keycode_to_name(48) == "Tab"
        assert keycode_to_name(49) == "space"
        assert keycode_to_name(50) == "grave"  # Backtick
        assert keycode_to_name(53) == "Escape"

    def test_keycode_to_name_function_keys(self):
        """Test conversion of function key codes."""
        from console_cowboy.utils.keycodes import keycode_to_name

        assert keycode_to_name(122) == "F1"
        assert keycode_to_name(120) == "F2"
        assert keycode_to_name(111) == "F12"

    def test_keycode_to_name_unknown(self):
        """Test that unknown key codes return None."""
        from console_cowboy.utils.keycodes import keycode_to_name

        assert keycode_to_name(999) is None
        assert keycode_to_name(-1) is None

    def test_modifiers_to_list_single(self):
        """Test conversion of single modifier flags."""
        from console_cowboy.utils.keycodes import (
            MACOS_MODIFIER_COMMAND,
            MACOS_MODIFIER_CONTROL,
            MACOS_MODIFIER_OPTION,
            MACOS_MODIFIER_SHIFT,
            modifiers_to_list,
        )

        assert modifiers_to_list(MACOS_MODIFIER_CONTROL) == ["ctrl"]
        assert modifiers_to_list(MACOS_MODIFIER_SHIFT) == ["shift"]
        assert modifiers_to_list(MACOS_MODIFIER_OPTION) == ["alt"]
        assert modifiers_to_list(MACOS_MODIFIER_COMMAND) == ["super"]

    def test_modifiers_to_list_combined(self):
        """Test conversion of combined modifier flags."""
        from console_cowboy.utils.keycodes import (
            MACOS_MODIFIER_COMMAND,
            MACOS_MODIFIER_CONTROL,
            MACOS_MODIFIER_SHIFT,
            modifiers_to_list,
        )

        # Ctrl+Shift+Cmd (1441792 from user's iTerm2 config)
        combined = (
            MACOS_MODIFIER_CONTROL | MACOS_MODIFIER_SHIFT | MACOS_MODIFIER_COMMAND
        )
        assert combined == 1441792
        mods = modifiers_to_list(combined)
        assert mods == ["ctrl", "shift", "super"]

    def test_modifiers_to_list_empty(self):
        """Test conversion of no modifiers."""
        from console_cowboy.utils.keycodes import modifiers_to_list

        assert modifiers_to_list(0) == []
        assert modifiers_to_list(None) == []

    def test_macos_hotkey_to_keybind_basic(self):
        """Test full hotkey to keybind conversion."""
        from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

        # Ctrl+Shift+Cmd+X (user's actual hotkey)
        result = macos_hotkey_to_keybind(7, 1441792)
        assert result == "global:ctrl+shift+super+x=toggle_quick_terminal"

    def test_macos_hotkey_to_keybind_grave(self):
        """Test conversion with grave/backtick key."""
        from console_cowboy.utils.keycodes import (
            MACOS_MODIFIER_CONTROL,
            macos_hotkey_to_keybind,
        )

        result = macos_hotkey_to_keybind(50, MACOS_MODIFIER_CONTROL)
        assert result == "global:ctrl+grave=toggle_quick_terminal"

    def test_macos_hotkey_to_keybind_no_modifiers(self):
        """Test conversion with no modifiers."""
        from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

        result = macos_hotkey_to_keybind(122, 0)  # F1
        assert result == "global:F1=toggle_quick_terminal"

    def test_macos_hotkey_to_keybind_unknown_keycode(self):
        """Test conversion with unknown key code returns None."""
        from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

        result = macos_hotkey_to_keybind(999, 0)
        assert result is None

    def test_macos_hotkey_to_keybind_custom_action(self):
        """Test conversion with custom action."""
        from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

        result = macos_hotkey_to_keybind(7, 0, action="custom_action")
        assert result == "global:x=custom_action"

    def test_macos_hotkey_to_keybind_application_scope(self):
        """Test conversion with application scope."""
        from console_cowboy.utils.keycodes import macos_hotkey_to_keybind

        result = macos_hotkey_to_keybind(7, 0, scope="application")
        assert result == "x=toggle_quick_terminal"
