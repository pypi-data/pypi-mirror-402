"""Tests for text hints/smart selection configuration."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    TextHintAction,
    TextHintBinding,
    TextHintConfig,
    TextHintMouseBinding,
    TextHintPrecision,
    TextHintRule,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    ITerm2Adapter,
    KittyAdapter,
    WeztermAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTextHints:
    """Tests for text hints/smart selection configuration."""

    def test_alacritty_parse_hints(self):
        """Test parsing Alacritty hints from TOML content."""
        content = """
[hints]
alphabet = "jfkdls;ahgurieowpq"

[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "xdg-open"
post_processing = true
binding = { key = "U", mods = "Control+Shift" }
mouse = { mods = "Control", enabled = true }

[[hints.enabled]]
regex = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+"
action = "Copy"
binding = { key = "E", mods = "Control+Shift" }
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=content)

        assert ctec.text_hints is not None
        assert ctec.text_hints.enabled is True
        assert ctec.text_hints.alphabet == "jfkdls;ahgurieowpq"
        assert len(ctec.text_hints.rules) == 2

        # First rule - URL hint
        rule1 = ctec.text_hints.rules[0]
        assert "https" in rule1.regex
        assert rule1.hyperlinks is True
        assert rule1.command == "xdg-open"
        assert rule1.post_processing is True
        assert rule1.binding.key == "U"
        assert "Control" in rule1.binding.mods
        assert rule1.mouse.enabled is True

        # Second rule - email hint
        rule2 = ctec.text_hints.rules[1]
        assert "@" in rule2.regex
        assert rule2.action == TextHintAction.COPY

    def test_alacritty_export_hints(self):
        """Test exporting hints to Alacritty format."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                alphabet="asdfgh",
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        hyperlinks=True,
                        command="open",
                        post_processing=True,
                        binding=TextHintBinding(key="O", mods=["Control", "Shift"]),
                        mouse=TextHintMouseBinding(mods=["Control"], enabled=True),
                    ),
                    TextHintRule(
                        regex="\\d{4}-\\d{2}-\\d{2}",
                        action=TextHintAction.COPY,
                    ),
                ],
            )
        )

        output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[hints]" in output
        assert 'alphabet = "asdfgh"' in output
        assert "[[hints.enabled]]" in output
        assert "https?://" in output
        assert 'command = "open"' in output
        assert "post_processing = true" in output

    def test_alacritty_hints_roundtrip(self):
        """Test Alacritty hints survive round-trip conversion."""
        content = """
[hints]
alphabet = "jfkdls"

[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "open"
post_processing = true
binding = { key = "O", mods = "Control+Shift" }
"""
        original = AlacrittyAdapter.parse("test.toml", content=content)
        exported = AlacrittyAdapter.export(original, use_toml=True)
        restored = AlacrittyAdapter.parse("test.toml", content=exported)

        assert restored.text_hints is not None
        assert restored.text_hints.alphabet == original.text_hints.alphabet
        assert len(restored.text_hints.rules) == len(original.text_hints.rules)

        orig_rule = original.text_hints.rules[0]
        rest_rule = restored.text_hints.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.hyperlinks == orig_rule.hyperlinks
        assert rest_rule.command == orig_rule.command
        assert rest_rule.post_processing == orig_rule.post_processing

    def test_iterm2_parse_smart_selection(self):
        """Test parsing iTerm2 Smart Selection Rules from plist content."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Smart Selection Rules": [
                {
                    "regex": "(https?://|www\\.)[^\\s]+",
                    "precision": 3,  # HIGH
                    "notes": "URL detection",
                    "actions": [{"title": "Open URL", "action": ""}],
                },
                {
                    "regex": "/[a-zA-Z0-9._/-]+",
                    "precision": 2,  # NORMAL
                    "notes": "File path detection",
                    "actions": [{"title": "Run Command...", "action": "open -R \\0"}],
                },
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)

        assert ctec.text_hints is not None
        assert ctec.text_hints.enabled is True
        assert len(ctec.text_hints.rules) == 2

        # First rule - URL
        rule1 = ctec.text_hints.rules[0]
        assert "https" in rule1.regex
        assert rule1.precision == TextHintPrecision.HIGH
        assert rule1.notes == "URL detection"
        assert rule1.action == TextHintAction.OPEN_URL

        # Second rule - file path
        rule2 = ctec.text_hints.rules[1]
        assert "/" in rule2.regex
        assert rule2.precision == TextHintPrecision.NORMAL
        assert rule2.action == TextHintAction.RUN_COMMAND
        assert rule2.parameter == "open -R \\0"

    def test_iterm2_export_smart_selection(self):
        """Test exporting text hints to iTerm2 Smart Selection Rules."""
        import plistlib

        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        precision=TextHintPrecision.HIGH,
                        notes="URL detection",
                        action=TextHintAction.OPEN_URL,
                    ),
                    TextHintRule(
                        regex="/[a-zA-Z0-9._/-]+",
                        precision=TextHintPrecision.NORMAL,
                        notes="File path",
                        action=TextHintAction.RUN_COMMAND,
                        command="open -R",
                    ),
                ],
            )
        )

        output = ITerm2Adapter.export(ctec)
        data = plistlib.loads(output.encode())

        profile = data["New Bookmarks"][0]
        assert "Smart Selection Rules" in profile

        rules = profile["Smart Selection Rules"]
        assert len(rules) == 2

        assert "https" in rules[0]["regex"]
        assert rules[0]["precision"] == 3  # HIGH
        assert rules[0]["actions"][0]["title"] == "Open URL"

    def test_iterm2_smart_selection_roundtrip(self):
        """Test iTerm2 Smart Selection Rules survive round-trip."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Default Bookmark": "Yes",
            "Smart Selection Rules": [
                {
                    "regex": "(https?://)[^\\s]+",
                    "precision": 4,  # VERY_HIGH
                    "notes": "HTTP URL",
                    "actions": [{"title": "Open URL", "action": ""}],
                }
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        original = ITerm2Adapter.parse("test.plist", content=content)
        exported = ITerm2Adapter.export(original)
        restored = ITerm2Adapter.parse("test.plist", content=exported)

        assert restored.text_hints is not None
        assert len(restored.text_hints.rules) == len(original.text_hints.rules)

        orig_rule = original.text_hints.rules[0]
        rest_rule = restored.text_hints.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.precision == orig_rule.precision
        assert rest_rule.action == orig_rule.action

    def test_alacritty_to_iterm2_hints(self):
        """Test converting hints from Alacritty to iTerm2."""
        import plistlib

        alacritty_content = """
[hints]
[[hints.enabled]]
regex = "https?://[^\\\\s]+"
hyperlinks = true
command = "open"
post_processing = true
"""
        ctec = AlacrittyAdapter.parse("test.toml", content=alacritty_content)

        iterm_output = ITerm2Adapter.export(ctec)
        iterm_data = plistlib.loads(iterm_output.encode())

        profile = iterm_data["New Bookmarks"][0]
        assert "Smart Selection Rules" in profile

        rules = profile["Smart Selection Rules"]
        assert len(rules) == 1
        assert "https" in rules[0]["regex"]

    def test_iterm2_to_alacritty_hints(self):
        """Test converting hints from iTerm2 to Alacritty."""
        import plistlib

        profile_data = {
            "Name": "Test",
            "Guid": "test-guid",
            "Smart Selection Rules": [
                {
                    "regex": "https?://[^\\s]+",
                    "precision": 3,
                    "actions": [{"title": "Copy", "action": ""}],
                }
            ],
        }

        plist_data = {"New Bookmarks": [profile_data]}
        content = plistlib.dumps(plist_data).decode()

        ctec = ITerm2Adapter.parse("test.plist", content=content)
        alacritty_output = AlacrittyAdapter.export(ctec, use_toml=True)

        assert "[hints]" in alacritty_output
        # tomli_w outputs inline tables, not [[hints.enabled]] syntax
        assert "enabled = [" in alacritty_output
        assert "https" in alacritty_output
        assert "Copy" in alacritty_output

    def test_kitty_warns_about_unsupported_hints(self):
        """Test that Kitty export warns about unsupported hints."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(regex="https?://[^\\s]+"),
                    TextHintRule(regex="[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+"),
                ],
            )
        )

        KittyAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("hint" in w.lower() for w in ctec.warnings)
        assert any("2" in w for w in ctec.warnings)  # Number of rules

    def test_ghostty_warns_about_unsupported_hints(self):
        """Test that Ghostty export warns about unsupported hints."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[TextHintRule(regex="https?://[^\\s]+")],
            )
        )

        GhosttyAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("hint" in w.lower() for w in ctec.warnings)

    def test_wezterm_exports_hyperlink_rules(self):
        """Test that WezTerm exports URL hints as hyperlink_rules."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="https?://[^\\s]+",
                        action=TextHintAction.OPEN,
                        hyperlinks=True,
                    )
                ],
            )
        )

        output = WeztermAdapter.export(ctec)

        assert "hyperlink_rules" in output
        assert "wezterm.default_hyperlink_rules()" in output
        assert "table.insert" in output
        assert "https" in output

    def test_wezterm_warns_about_non_url_hints(self):
        """Test that WezTerm warns about hints with non-URL actions."""
        ctec = CTEC(
            text_hints=TextHintConfig(
                enabled=True,
                rules=[
                    TextHintRule(
                        regex="[a-z]+@[a-z]+",
                        action=TextHintAction.COPY,  # Can't be a hyperlink
                    )
                ],
            )
        )

        WeztermAdapter.export(ctec)

        assert len(ctec.warnings) > 0
        assert any("Copy" in w or "action" in w.lower() for w in ctec.warnings)

    def test_wezterm_parses_hyperlink_rules(self):
        """Test that WezTerm parses hyperlink_rules into text hints.

        Uses a Lua interpreter with a mock wezterm object for accurate parsing.
        """
        content = """
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.hyperlink_rules = {
  { regex = [[https?://[^\\s]+]], format = "$0" },
  { regex = "task-(\\\\d+)", format = "https://example.com/task/$1" },
}

return config
"""
        ctec = WeztermAdapter.parse("test.lua", content=content)

        assert ctec.text_hints is not None
        assert len(ctec.text_hints.rules) == 2
        assert ctec.text_hints.rules[0].regex == "https?://[^\\s]+"
        assert ctec.text_hints.rules[0].action == TextHintAction.OPEN
        assert ctec.text_hints.rules[1].parameter == "https://example.com/task/$1"

    def test_text_hint_config_serialization(self):
        """Test TextHintConfig to_dict and from_dict."""
        config = TextHintConfig(
            enabled=True,
            alphabet="asdfgh",
            rules=[
                TextHintRule(
                    regex="https?://[^\\s]+",
                    hyperlinks=True,
                    action=TextHintAction.OPEN,
                    command="open",
                    post_processing=True,
                    persist=False,
                    binding=TextHintBinding(key="O", mods=["Control", "Shift"]),
                    mouse=TextHintMouseBinding(mods=["Control"], enabled=True),
                    precision=TextHintPrecision.HIGH,
                    notes="URL detection",
                    parameter="\\0",
                )
            ],
        )

        dict_repr = config.to_dict()
        restored = TextHintConfig.from_dict(dict_repr)

        assert restored.enabled == config.enabled
        assert restored.alphabet == config.alphabet
        assert len(restored.rules) == 1

        orig_rule = config.rules[0]
        rest_rule = restored.rules[0]
        assert rest_rule.regex == orig_rule.regex
        assert rest_rule.hyperlinks == orig_rule.hyperlinks
        assert rest_rule.action == orig_rule.action
        assert rest_rule.command == orig_rule.command
        assert rest_rule.post_processing == orig_rule.post_processing
        assert rest_rule.persist == orig_rule.persist
        assert rest_rule.binding.key == orig_rule.binding.key
        assert rest_rule.binding.mods == orig_rule.binding.mods
        assert rest_rule.mouse.mods == orig_rule.mouse.mods
        assert rest_rule.mouse.enabled == orig_rule.mouse.enabled
        assert rest_rule.precision == orig_rule.precision
        assert rest_rule.notes == orig_rule.notes
        assert rest_rule.parameter == orig_rule.parameter
