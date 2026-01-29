"""Tests for the iTerm2 adapter."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    BehaviorConfig,
    Color,
    ColorScheme,
    CursorConfig,
    CursorStyle,
    FontConfig,
)
from console_cowboy.terminals import GhosttyAdapter, ITerm2Adapter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestITerm2Adapter:
    """Tests for the iTerm2 adapter."""

    def test_adapter_metadata(self):
        assert ITerm2Adapter.name == "iterm2"
        assert ".plist" in ITerm2Adapter.config_extensions

    def test_parse_fixture(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        assert ctec.source_terminal == "iterm2"
        assert ctec.window.columns == 120
        assert ctec.window.rows == 200

    def test_parse_default_profile(self):
        """Test that the default profile settings are imported correctly."""
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        # Settings from the default profile should be at the CTEC level
        assert ctec.color_scheme is not None
        assert ctec.font is not None or ctec.cursor is not None

    def test_parse_colors(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        assert ctec.color_scheme is not None
        assert ctec.color_scheme.foreground is not None

    def test_export(self):
        ctec = CTEC(
            font=FontConfig(family="Monaco", size=12.0),
            cursor=CursorConfig(style=CursorStyle.BLOCK, blink=True),
            color_scheme=ColorScheme(
                foreground=Color(255, 255, 255),
                background=Color(0, 0, 0),
            ),
        )
        output = ITerm2Adapter.export(ctec)

        # Should be valid plist XML
        assert '<?xml version="1.0"' in output
        assert "<plist" in output
        assert "Monaco" in output

    def test_terminal_specific_settings(self):
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        iterm_specific = ctec.get_terminal_specific("iterm2")
        assert len(iterm_specific) > 0

    def test_hotkey_profile_extraction(self):
        """Test that hotkey settings are extracted from a separate Hotkey Window profile."""
        config_path = FIXTURES_DIR / "iterm2" / "com.googlecode.iterm2.plist"
        ctec = ITerm2Adapter.parse(config_path)

        # The Default profile doesn't have hotkey settings, but the Hotkey Window profile does
        # The adapter should extract hotkey settings from the Hotkey Window profile
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.enabled is True
        assert ctec.quick_terminal.floating is True
        assert ctec.quick_terminal.animation_duration == 200
        assert ctec.quick_terminal.hotkey_key_code == 7  # 'X' key
        assert ctec.quick_terminal.hotkey_modifiers == 1441792  # Cmd+Option
        # Window Type 7 = Full Height Right of Screen
        from console_cowboy.ctec.schema import QuickTerminalPosition

        assert ctec.quick_terminal.position == QuickTerminalPosition.RIGHT

    def test_parse_ligatures(self):
        """Test that ASCII Ligatures setting is parsed into ctec.font.ligatures."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>Normal Font</key>
            <string>JetBrainsMono-Regular 14</string>
            <key>ASCII Ligatures</key>
            <true/>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        assert ctec.font is not None
        assert ctec.font.ligatures is True

    def test_parse_ligatures_disabled(self):
        """Test that ASCII Ligatures=false is parsed correctly."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>Normal Font</key>
            <string>JetBrainsMono-Regular 14</string>
            <key>ASCII Ligatures</key>
            <false/>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        assert ctec.font is not None
        assert ctec.font.ligatures is False

    def test_parse_ligatures_without_font(self):
        """Test that ASCII Ligatures works even without Normal Font."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>ASCII Ligatures</key>
            <true/>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        assert ctec.font is not None
        assert ctec.font.ligatures is True
        assert ctec.font.family is None

    def test_export_ligatures(self):
        """Test that ligatures setting is exported to ASCII Ligatures."""
        ctec = CTEC(font=FontConfig(family="JetBrains Mono", size=14.0, ligatures=True))
        output = ITerm2Adapter.export(ctec)
        assert "<key>ASCII Ligatures</key>" in output
        assert "<true/>" in output

    def test_export_ligatures_disabled(self):
        """Test that ligatures=False is exported correctly."""
        ctec = CTEC(
            font=FontConfig(family="JetBrains Mono", size=14.0, ligatures=False)
        )
        output = ITerm2Adapter.export(ctec)
        assert "<key>ASCII Ligatures</key>" in output
        assert "<false/>" in output

    def test_parse_option_key_sends(self):
        """Test that Option Key Sends is stored as terminal-specific."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>Option Key Sends</key>
            <integer>2</integer>
            <key>Right Option Key Sends</key>
            <integer>0</integer>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        # Should be stored as terminal-specific
        option_key = ctec.get_terminal_specific("iterm2", "Option Key Sends")
        assert option_key == 2
        right_option = ctec.get_terminal_specific("iterm2", "Right Option Key Sends")
        assert right_option == 0

    def test_parse_tab_color(self):
        """Test that Tab Color is stored as terminal-specific."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>Tab Color</key>
            <dict>
                <key>Red Component</key>
                <real>0.5</real>
                <key>Green Component</key>
                <real>0.25</real>
                <key>Blue Component</key>
                <real>0.75</real>
            </dict>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        tab_color = ctec.get_terminal_specific("iterm2", "Tab Color")
        assert tab_color is not None
        assert isinstance(tab_color, dict)
        assert tab_color["Red Component"] == 0.5

    def test_parse_terminal_type(self):
        """Test that Terminal Type is mapped to behavior.terminal_type."""
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>New Bookmarks</key>
    <array>
        <dict>
            <key>Name</key>
            <string>Default</string>
            <key>Default Bookmark</key>
            <string>Yes</string>
            <key>Terminal Type</key>
            <string>xterm-256color</string>
        </dict>
    </array>
</dict>
</plist>"""
        ctec = ITerm2Adapter.parse("test.plist", content=plist_content)
        # Terminal Type should map to terminal_type (first-class schema field)
        assert ctec.behavior is not None
        assert ctec.behavior.terminal_type == "xterm-256color"

    def test_export_terminal_type(self):
        """Test that terminal_type is exported as Terminal Type."""
        ctec = CTEC(behavior=BehaviorConfig(terminal_type="xterm-256color"))
        output = ITerm2Adapter.export(ctec)
        assert "<key>Terminal Type</key>" in output
        assert "<string>xterm-256color</string>" in output

    def test_roundtrip_terminal_type(self):
        """Test that Terminal Type round-trips correctly."""
        original = CTEC(behavior=BehaviorConfig(terminal_type="xterm-256color"))
        output = ITerm2Adapter.export(original)
        parsed = ITerm2Adapter.parse("test.plist", content=output)
        assert parsed.behavior.terminal_type == "xterm-256color"

    def test_roundtrip_ligatures(self):
        """Test that ligatures setting round-trips correctly."""
        original = CTEC(
            font=FontConfig(family="JetBrains Mono", size=14.0, ligatures=True)
        )
        output = ITerm2Adapter.export(original)
        parsed = ITerm2Adapter.parse("test.plist", content=output)
        assert parsed.font.ligatures is True

    def test_roundtrip_option_key_sends(self):
        """Test that Option Key Sends round-trips via terminal-specific."""
        original = CTEC()
        original.add_terminal_specific("iterm2", "Option Key Sends", 2)
        original.add_terminal_specific("iterm2", "Right Option Key Sends", 1)
        output = ITerm2Adapter.export(original)
        parsed = ITerm2Adapter.parse("test.plist", content=output)
        assert parsed.get_terminal_specific("iterm2", "Option Key Sends") == 2
        assert parsed.get_terminal_specific("iterm2", "Right Option Key Sends") == 1


class TestITerm2ToGhosttyQuickTerminalHotkey:
    """Tests for iTerm2 to Ghostty quick terminal hotkey conversion."""

    def test_ghostty_export_quick_terminal_with_hotkey(self):
        """Test Ghostty exports keybind for quick terminal hotkey from iTerm2."""
        from console_cowboy.ctec.schema import (
            QuickTerminalConfig,
            QuickTerminalPosition,
        )

        # Simulate iTerm2's Ctrl+Shift+Cmd+X hotkey
        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                position=QuickTerminalPosition.TOP,
                hotkey_key_code=7,  # X key
                hotkey_modifiers=1441792,  # Ctrl+Shift+Cmd
            )
        )
        output = GhosttyAdapter.export(ctec)

        # Should have the quick terminal position
        assert "quick-terminal-position = top" in output
        # Should have the keybind for toggle_quick_terminal
        assert "keybind = global:ctrl+shift+super+x=toggle_quick_terminal" in output

    def test_ghostty_export_quick_terminal_hotkey_grave(self):
        """Test Ghostty exports Ctrl+` hotkey correctly."""
        from console_cowboy.ctec.schema import QuickTerminalConfig
        from console_cowboy.utils.keycodes import MACOS_MODIFIER_CONTROL

        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                hotkey_key_code=50,  # Grave/backtick
                hotkey_modifiers=MACOS_MODIFIER_CONTROL,
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "keybind = global:ctrl+grave=toggle_quick_terminal" in output

    def test_ghostty_export_quick_terminal_warns_unknown_keycode(self):
        """Test Ghostty warns when key code cannot be converted."""
        from console_cowboy.ctec.schema import QuickTerminalConfig

        ctec = CTEC(
            quick_terminal=QuickTerminalConfig(
                enabled=True,
                hotkey_key_code=999,  # Unknown key code
                hotkey_modifiers=0,
            )
        )
        output = GhosttyAdapter.export(ctec)

        # Should have a warning about the conversion failure
        assert any("key code" in w.lower() for w in ctec.warnings)
        # Should NOT have a keybind line (since conversion failed)
        assert "keybind = " not in output

    def test_iterm2_to_ghostty_roundtrip_preserves_hotkey(self):
        """Test iTerm2 fixture with hotkey converts to Ghostty with keybind."""
        # Load the iTerm2 fixture which has a Hotkey Window profile
        from pathlib import Path

        fixture_path = (
            Path(__file__).parent / "fixtures/iterm2/com.googlecode.iterm2.plist"
        )
        ctec = ITerm2Adapter.parse(fixture_path)

        # The fixture should have a quick_terminal with hotkey info
        assert ctec.quick_terminal is not None
        assert ctec.quick_terminal.enabled is True
        assert ctec.quick_terminal.hotkey_key_code is not None

        # Export to Ghostty
        output = GhosttyAdapter.export(ctec)

        # Should have a keybind for toggle_quick_terminal
        assert "toggle_quick_terminal" in output
        assert "keybind = global:" in output

    def test_parse_copy_on_select(self):
        """Test that CopySelection global setting is parsed to copy_on_select."""
        import plistlib

        profile = {
            "Name": "Default",
            "Guid": "default",
        }
        plist_data = {
            "New Bookmarks": [profile],
            "CopySelection": True,
        }
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)
        assert ctec.behavior is not None
        assert ctec.behavior.copy_on_select is True

    def test_parse_copy_on_select_false(self):
        """Test that CopySelection=False is parsed correctly."""
        import plistlib

        profile = {
            "Name": "Default",
            "Guid": "default",
        }
        plist_data = {
            "New Bookmarks": [profile],
            "CopySelection": False,
        }
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)
        assert ctec.behavior is not None
        assert ctec.behavior.copy_on_select is False

    def test_export_copy_on_select(self):
        """Test that copy_on_select is exported as CopySelection."""
        ctec = CTEC(behavior=BehaviorConfig(copy_on_select=True))
        output = ITerm2Adapter.export(ctec)

        import plistlib

        data = plistlib.loads(output.encode())
        assert data.get("CopySelection") is True

    def test_roundtrip_copy_on_select(self):
        """Test that copy_on_select round-trips correctly."""
        original = CTEC(behavior=BehaviorConfig(copy_on_select=True))
        output = ITerm2Adapter.export(original)
        parsed = ITerm2Adapter.parse("test.plist", content=output)
        assert parsed.behavior.copy_on_select is True
