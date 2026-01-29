"""Tests for keybinding parsing and export across terminals."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    KeyBinding,
    KeyBindingScope,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    KittyAdapter,
    WeztermAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestKeyBindings:
    """Tests for keybinding parsing and export across terminals."""

    def test_ghostty_parse_basic_keybindings(self):
        """Test parsing basic Ghostty keybindings."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = ctrl+shift+v=paste_from_clipboard
keybind = ctrl+t=new_tab
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 3

        # Check first binding
        kb1 = ctec.key_bindings[0]
        assert kb1.action == "copy_to_clipboard"
        assert kb1.key == "c"
        assert "ctrl" in kb1.mods
        assert "shift" in kb1.mods

        # Check third binding (no modifiers except ctrl)
        kb3 = ctec.key_bindings[2]
        assert kb3.action == "new_tab"
        assert kb3.key == "t"
        assert kb3.mods == ["ctrl"]

    def test_ghostty_parse_action_with_parameter(self):
        """Test parsing Ghostty keybindings with action parameters."""
        content = """
keybind = ctrl+shift+enter=new_split:right
keybind = ctrl+shift+minus=new_split:down
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 2

        kb1 = ctec.key_bindings[0]
        assert kb1.action == "new_split"
        assert kb1.action_param == "right"
        assert kb1.get_full_action() == "new_split:right"

        kb2 = ctec.key_bindings[1]
        assert kb2.action == "new_split"
        assert kb2.action_param == "down"

    def test_ghostty_parse_global_keybinding(self):
        """Test parsing Ghostty global keybindings."""
        content = """
keybind = global:ctrl+grave=toggle_quick_terminal
keybind = global:super+space=toggle_quick_terminal
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 2

        kb1 = ctec.key_bindings[0]
        assert kb1.scope == KeyBindingScope.GLOBAL
        assert kb1.action == "toggle_quick_terminal"
        assert kb1.key == "grave"
        assert kb1.mods == ["ctrl"]

    def test_ghostty_parse_unconsumed_keybinding(self):
        """Test parsing Ghostty unconsumed keybindings."""
        content = """
keybind = unconsumed:ctrl+shift+g=write_screen_file
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.scope == KeyBindingScope.UNCONSUMED
        assert kb.consume is False
        assert kb.action == "write_screen_file"

    def test_ghostty_parse_key_sequence(self):
        """Test parsing Ghostty key sequences (leader keys)."""
        content = """
keybind = ctrl+a>n=new_window
keybind = ctrl+a>t=new_tab
keybind = ctrl+b>ctrl+c=close_tab
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 3

        # First key sequence
        kb1 = ctec.key_bindings[0]
        assert kb1.key_sequence == ["ctrl+a", "n"]
        assert kb1.action == "new_window"
        # The key/mods represent the last key in the sequence
        assert kb1.key == "n"
        assert kb1.mods == []

        # Third key sequence with modifier on second key
        kb3 = ctec.key_bindings[2]
        assert kb3.key_sequence == ["ctrl+b", "ctrl+c"]
        assert kb3.key == "c"
        assert kb3.mods == ["ctrl"]

    def test_ghostty_parse_physical_key(self):
        """Test parsing Ghostty physical key bindings."""
        content = """
keybind = physical:ctrl+grave=toggle_quick_terminal
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.physical_key is True
        assert kb.action == "toggle_quick_terminal"

    def test_ghostty_parse_all_scope(self):
        """Test parsing Ghostty 'all:' scope keybindings."""
        content = """
keybind = all:ctrl+shift+p=command_palette
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        assert len(ctec.key_bindings) == 1

        kb = ctec.key_bindings[0]
        assert kb.scope == KeyBindingScope.ALL
        assert kb.action == "command_palette"

    def test_ghostty_parse_unbind(self):
        """Test that Ghostty unbind keybindings are stored as terminal-specific."""
        content = """
keybind = ctrl+c=unbind
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        # Unbind should not create a KeyBinding
        assert len(ctec.key_bindings) == 0

        # Should be stored as terminal-specific
        ghostty_specific = ctec.get_terminal_specific("ghostty")
        unbind_settings = [s for s in ghostty_specific if "keybind_unbind" in s.key]
        assert len(unbind_settings) == 1

    def test_ghostty_export_basic_keybindings(self):
        """Test exporting basic keybindings to Ghostty format."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(action="copy_to_clipboard", key="c", mods=["ctrl", "shift"]),
                KeyBinding(
                    action="paste_from_clipboard", key="v", mods=["ctrl", "shift"]
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+c=copy_to_clipboard" in output
        assert "keybind = ctrl+shift+v=paste_from_clipboard" in output

    def test_ghostty_export_action_with_parameter(self):
        """Test exporting keybindings with action parameters."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_split",
                    key="enter",
                    mods=["ctrl", "shift"],
                    action_param="right",
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+enter=new_split:right" in output

    def test_ghostty_export_global_keybinding(self):
        """Test exporting global keybindings."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = global:ctrl+grave=toggle_quick_terminal" in output

    def test_ghostty_export_key_sequence(self):
        """Test exporting key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+a>n=new_window" in output

    def test_ghostty_keybinding_roundtrip(self):
        """Test that Ghostty keybindings survive round-trip conversion."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = global:ctrl+grave=toggle_quick_terminal
keybind = ctrl+shift+enter=new_split:right
keybind = ctrl+a>n=new_window
"""
        original = GhosttyAdapter.parse("test", content=content)
        exported = GhosttyAdapter.export(original)
        restored = GhosttyAdapter.parse("test", content=exported)

        assert len(restored.key_bindings) == len(original.key_bindings)

        # Check specific bindings are preserved
        for i, (orig, rest) in enumerate(
            zip(original.key_bindings, restored.key_bindings, strict=False)
        ):
            assert rest.action == orig.action, f"Action mismatch at index {i}"
            assert rest.key == orig.key, f"Key mismatch at index {i}"
            assert rest.mods == orig.mods, f"Mods mismatch at index {i}"
            assert rest.action_param == orig.action_param, (
                f"Param mismatch at index {i}"
            )
            assert rest.scope == orig.scope, f"Scope mismatch at index {i}"

    def test_ghostty_fixture_keybindings(self):
        """Test parsing keybindings from the Ghostty fixture file."""
        config_path = FIXTURES_DIR / "ghostty" / "config"
        ctec = GhosttyAdapter.parse(config_path)

        assert len(ctec.key_bindings) > 0

        # Check for global keybinding
        global_kb = next(
            (kb for kb in ctec.key_bindings if kb.scope == KeyBindingScope.GLOBAL),
            None,
        )
        assert global_kb is not None
        assert global_kb.action == "toggle_quick_terminal"

        # Check for action with parameter
        param_kb = next(
            (kb for kb in ctec.key_bindings if kb.action_param is not None), None
        )
        assert param_kb is not None
        assert param_kb.action == "new_split"
        assert param_kb.action_param == "right"

        # Check for key sequence
        seq_kb = next(
            (kb for kb in ctec.key_bindings if kb.key_sequence is not None), None
        )
        assert seq_kb is not None
        assert "ctrl+a" in seq_kb.key_sequence

    def test_alacritty_keybindings_with_mode(self):
        """Test Alacritty keybindings with mode field."""
        content = """
[[keyboard.bindings]]
key = "V"
mods = "Control+Shift"
action = "Paste"
mode = "~Vi"

[[keyboard.bindings]]
key = "Escape"
action = "ToggleViMode"
mode = "~Vi"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        assert len(ctec.key_bindings) == 2

        # Check mode is parsed
        kb1 = ctec.key_bindings[0]
        assert kb1.mode == "~Vi"
        assert kb1.action == "Paste"

        kb2 = ctec.key_bindings[1]
        assert kb2.mode == "~Vi"

    def test_alacritty_export_keybindings_with_mode(self):
        """Test Alacritty exports keybindings with mode field."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="V",
                    mods=["Control", "Shift"],
                    mode="~Vi",
                ),
            ]
        )
        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert 'mode = "~Vi"' in output

    def test_kitty_keybinding_export_with_action_param(self):
        """Test Kitty exports keybindings with action parameters (space-separated)."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="enter",
                    mods=["ctrl", "shift"],
                    action_param="--cwd=current",
                ),
            ]
        )
        output = KittyAdapter.export(ctec)

        # Kitty uses space-separated action parameters, not colon
        assert "map ctrl+shift+enter new_window --cwd=current" in output

    def test_keybinding_schema_serialization(self):
        """Test KeyBinding to_dict and from_dict with all fields."""
        kb = KeyBinding(
            action="new_split",
            key="enter",
            mods=["ctrl", "shift"],
            action_param="right",
            scope=KeyBindingScope.GLOBAL,
            key_sequence=["ctrl+a", "n"],
            mode="~Vi",
            physical_key=True,
            consume=False,
            _raw="global:ctrl+shift+enter=new_split:right",
        )

        dict_repr = kb.to_dict()
        restored = KeyBinding.from_dict(dict_repr)

        assert restored.action == kb.action
        assert restored.key == kb.key
        assert restored.mods == kb.mods
        assert restored.action_param == kb.action_param
        assert restored.scope == kb.scope
        assert restored.key_sequence == kb.key_sequence
        assert restored.mode == kb.mode
        assert restored.physical_key == kb.physical_key
        assert restored.consume == kb.consume
        assert restored._raw == kb._raw

    def test_cross_terminal_keybinding_conversion_ghostty_to_alacritty(self):
        """Test converting keybindings from Ghostty to Alacritty."""
        content = """
keybind = ctrl+shift+c=copy_to_clipboard
keybind = ctrl+shift+v=paste_from_clipboard
"""
        ctec = GhosttyAdapter.parse("test", content=content)

        alacritty_output = AlacrittyAdapter.export(ctec, use_toml=True)

        # Check that keybindings are in the output
        assert "keyboard" in alacritty_output
        assert "bindings" in alacritty_output
        assert "copy_to_clipboard" in alacritty_output
        assert "paste_from_clipboard" in alacritty_output

    def test_cross_terminal_keybinding_conversion_alacritty_to_ghostty(self):
        """Test converting keybindings from Alacritty to Ghostty."""
        content = """
[[keyboard.bindings]]
key = "V"
mods = "Control+Shift"
action = "Paste"

[[keyboard.bindings]]
key = "C"
mods = "Control+Shift"
action = "Copy"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        ghostty_output = GhosttyAdapter.export(ctec)

        assert "keybind = " in ghostty_output
        assert "Paste" in ghostty_output
        assert "Copy" in ghostty_output

    def test_cross_terminal_keybinding_kitty_to_ghostty(self):
        """Test converting keybindings from Kitty to Ghostty."""
        content = """
map ctrl+shift+c copy_to_clipboard
map ctrl+shift+v paste_from_clipboard
"""
        ctec = KittyAdapter.parse("test.conf", content=content)

        ghostty_output = GhosttyAdapter.export(ctec)

        assert "keybind = ctrl+shift+c=copy_to_clipboard" in ghostty_output
        assert "keybind = ctrl+shift+v=paste_from_clipboard" in ghostty_output

    def test_alacritty_keybinding_with_chars_field(self):
        """Test Alacritty keybindings using chars field are preserved as terminal-specific."""
        content = """
[[keyboard.bindings]]
key = "T"
mods = "Control+Shift"
chars = "\\x1b[13;5u"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        # chars-based binding should not be in key_bindings
        assert len(ctec.key_bindings) == 0

        # But should be in terminal_specific with a warning
        specific = ctec.get_terminal_specific("alacritty")
        assert len(specific) == 1
        assert "chars:" in specific[0].key
        # TOML parser interprets escape sequences, so the actual escape character is stored
        assert "\x1b[13;5u" in specific[0].value

        # Warning should be added
        assert len(ctec.warnings) == 1
        assert "chars" in ctec.warnings[0]

    def test_alacritty_keybinding_with_command_field(self):
        """Test Alacritty keybindings using command field are preserved as terminal-specific."""
        content = """
[[keyboard.bindings]]
key = "N"
mods = "Control+Shift"
command = "alacritty msg create-window"
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        # command-based binding should not be in key_bindings
        assert len(ctec.key_bindings) == 0

        # But should be in terminal_specific with a warning
        specific = ctec.get_terminal_specific("alacritty")
        assert len(specific) == 1
        assert "command:" in specific[0].key

        # Warning should be added
        assert len(ctec.warnings) == 1
        assert "command" in ctec.warnings[0]

    def test_kitty_parse_key_sequence(self):
        """Test Kitty parses key sequences (leader keys) with > separator."""
        content = """
map ctrl+a>n new_window
map ctrl+x>ctrl+y>z some_action
"""
        ctec = KittyAdapter.parse("test.conf", content=content)

        assert len(ctec.key_bindings) == 2

        # First keybinding: ctrl+a>n
        kb1 = ctec.key_bindings[0]
        assert kb1.key_sequence == ["ctrl+a", "n"]
        assert kb1.action == "new_window"
        assert kb1.key == "n"
        assert kb1.mods == []

        # Second keybinding: ctrl+x>ctrl+y>z
        kb2 = ctec.key_bindings[1]
        assert kb2.key_sequence == ["ctrl+x", "ctrl+y", "z"]
        assert kb2.action == "some_action"
        assert kb2.key == "z"
        assert kb2.mods == []

    def test_kitty_export_key_sequence(self):
        """Test Kitty exports key sequences correctly."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        output = KittyAdapter.export(ctec)

        assert "map ctrl+a>n new_window" in output

    def test_alacritty_export_warns_about_key_sequences(self):
        """Test Alacritty export warns when keybindings have key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="new_window",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        AlacrittyAdapter.export(ctec)

        # Warning should be added about unsupported key sequences
        assert len(ctec.warnings) == 1
        assert "key sequence" in ctec.warnings[0].lower()
        assert "ctrl+a>n" in ctec.warnings[0]

    def test_alacritty_export_warns_about_global_scope(self):
        """Test Alacritty export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        AlacrittyAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()

    def test_kitty_export_warns_about_global_scope(self):
        """Test Kitty export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="toggle_quick_terminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        KittyAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()

    def test_kitty_export_warns_about_mode_restrictions(self):
        """Test Kitty export warns when keybindings have mode restrictions."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="v",
                    mods=["ctrl", "shift"],
                    mode="~Vi",
                ),
            ]
        )
        KittyAdapter.export(ctec)

        # Warning should be added about unsupported mode
        assert len(ctec.warnings) == 1
        assert "mode" in ctec.warnings[0].lower()
        assert "~Vi" in ctec.warnings[0]

    def test_ghostty_export_warns_about_mode_restrictions(self):
        """Test Ghostty export warns when keybindings have mode restrictions."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="Paste",
                    key="v",
                    mods=["ctrl", "shift"],
                    mode="~Vi",
                ),
            ]
        )
        GhosttyAdapter.export(ctec)

        # Warning should be added about unsupported mode
        assert len(ctec.warnings) == 1
        assert "mode" in ctec.warnings[0].lower()

    def test_wezterm_export_warns_about_key_sequences(self):
        """Test WezTerm export warns when keybindings have key sequences."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="NewWindow",
                    key="n",
                    mods=[],
                    key_sequence=["ctrl+a", "n"],
                ),
            ]
        )
        WeztermAdapter.export(ctec)

        # Warning should be added about unsupported key sequences
        assert len(ctec.warnings) == 1
        assert "key sequence" in ctec.warnings[0].lower()

    def test_wezterm_export_warns_about_global_scope(self):
        """Test WezTerm export warns when keybindings have global scope."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(
                    action="ToggleQuickTerminal",
                    key="grave",
                    mods=["ctrl"],
                    scope=KeyBindingScope.GLOBAL,
                ),
            ]
        )
        WeztermAdapter.export(ctec)

        # Warning should be added about unsupported global scope
        assert len(ctec.warnings) == 1
        assert "global" in ctec.warnings[0].lower()
