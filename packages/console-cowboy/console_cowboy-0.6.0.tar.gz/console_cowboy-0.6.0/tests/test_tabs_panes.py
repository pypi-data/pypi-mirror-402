"""Tests for tab and pane configuration across terminals."""

from pathlib import Path

from console_cowboy.ctec.schema import (
    CTEC,
    KeyBinding,
)
from console_cowboy.terminals import (
    AlacrittyAdapter,
    GhosttyAdapter,
    KittyAdapter,
    WeztermAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestTabsAndPanes:
    """Tests for tab and pane configuration across terminals."""

    def test_ghostty_parse_tabs(self):
        """Test Ghostty parses tab settings."""
        config = """
window-show-tab-bar = always
gtk-tabs-location = bottom
window-new-tab-position = end
window-inherit-working-directory = true
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.visibility.value == "always"
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.new_tab_position.value == "end"
        assert ctec.tabs.inherit_working_directory is True

    def test_ghostty_parse_panes(self):
        """Test Ghostty parses pane settings."""
        config = """
unfocused-split-opacity = 0.8
unfocused-split-fill = #333333
split-divider-color = #444444
focus-follows-mouse = true
"""
        ctec = GhosttyAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.8
        assert ctec.panes.inactive_dim_color.to_hex() == "#333333"
        assert ctec.panes.divider_color.to_hex() == "#444444"
        assert ctec.panes.focus_follows_mouse is True

    def test_ghostty_export_tabs(self):
        """Test Ghostty exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarVisibility,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                visibility=TabBarVisibility.AUTO,
                position=TabBarPosition.BOTTOM,
                inherit_working_directory=True,
            )
        )
        output = GhosttyAdapter.export(ctec)
        assert "window-show-tab-bar = auto" in output
        assert "gtk-tabs-location = bottom" in output
        assert "window-inherit-working-directory = true" in output

    def test_ghostty_export_panes_clamps_dim_factor(self):
        """Test Ghostty clamps dim factor to minimum 0.15."""
        from console_cowboy.ctec.schema import PaneConfig

        ctec = CTEC(panes=PaneConfig(inactive_dim_factor=0.1))
        output = GhosttyAdapter.export(ctec)
        assert "unfocused-split-opacity = 0.15" in output
        assert any("0.15" in w and "clamp" in w.lower() for w in ctec.warnings)

    def test_kitty_parse_tabs(self):
        """Test Kitty parses tab settings."""
        config = """
tab_bar_edge bottom
tab_bar_style powerline
tab_bar_align center
tab_bar_min_tabs 2
tab_switch_strategy previous
active_tab_foreground #ffffff
active_tab_background #000000
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.style.value == "powerline"
        # Kitty-specific settings are stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "tab_bar_align") == "center"
        assert ctec.get_terminal_specific("kitty", "tab_switch_strategy") == "previous"
        assert ctec.get_terminal_specific("kitty", "tab_bar_min_tabs") == 2
        assert ctec.tabs.active_foreground.to_hex() == "#ffffff"
        assert ctec.tabs.active_background.to_hex() == "#000000"

    def test_kitty_parse_hidden_tabs(self):
        """Test Kitty parses tab_bar_style=hidden as visibility=NEVER."""
        config = """
tab_bar_style hidden
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.visibility.value == "never"

    def test_kitty_parse_panes(self):
        """Test Kitty parses pane settings."""
        config = """
inactive_text_alpha 0.7
active_border_color #00ff00
inactive_border_color #555555
window_border_width 1.5pt
focus_follows_mouse yes
"""
        ctec = KittyAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.7
        assert ctec.panes.focus_follows_mouse is True
        # Kitty-specific border settings are stored in terminal_specific
        assert ctec.get_terminal_specific("kitty", "active_border_color") == "#00ff00"
        assert ctec.get_terminal_specific("kitty", "inactive_border_color") == "#555555"
        assert ctec.get_terminal_specific("kitty", "window_border_width") == "1.5pt"

    def test_kitty_export_tabs(self):
        """Test Kitty exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarStyle,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                position=TabBarPosition.BOTTOM,
                style=TabBarStyle.POWERLINE,
            )
        )
        # Add Kitty-specific alignment via terminal_specific
        ctec.add_terminal_specific("kitty", "tab_bar_align", "center")
        output = KittyAdapter.export(ctec)
        assert "tab_bar_edge bottom" in output
        assert "tab_bar_style powerline" in output
        assert "tab_bar_align center" in output

    def test_wezterm_parse_tabs(self):
        """Test WezTerm parses tab settings."""
        config = """
local wezterm = require "wezterm"
local config = wezterm.config_builder()
config.enable_tab_bar = true
config.tab_bar_at_bottom = true
config.use_fancy_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.tab_max_width = 25
config.show_tab_index_in_tab_bar = true
return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.tabs is not None
        assert ctec.tabs.position.value == "bottom"
        assert ctec.tabs.style.value == "fancy"
        assert ctec.tabs.auto_hide_single is True
        assert ctec.tabs.max_width == 25
        assert ctec.tabs.show_index is True

    def test_wezterm_parse_panes(self):
        """Test WezTerm parses pane settings."""
        config = """
local wezterm = require "wezterm"
local config = wezterm.config_builder()
config.inactive_pane_hsb = {
  saturation = 1.0,
  brightness = 0.7,
}
config.pane_focus_follows_mouse = true
config.colors = {
  split = "#444444",
}
return config
"""
        ctec = WeztermAdapter.parse("test", content=config)
        assert ctec.panes is not None
        assert ctec.panes.inactive_dim_factor == 0.7
        assert ctec.panes.focus_follows_mouse is True
        assert ctec.panes.divider_color.to_hex() == "#444444"

    def test_wezterm_export_tabs(self):
        """Test WezTerm exports tab settings."""
        from console_cowboy.ctec.schema import (
            TabBarPosition,
            TabBarStyle,
            TabConfig,
        )

        ctec = CTEC(
            tabs=TabConfig(
                position=TabBarPosition.BOTTOM,
                style=TabBarStyle.FANCY,
                auto_hide_single=True,
            )
        )
        output = WeztermAdapter.export(ctec)
        assert "config.tab_bar_at_bottom = true" in output
        assert "config.use_fancy_tab_bar = true" in output
        assert "config.hide_tab_bar_if_only_one_tab = true" in output

    def test_alacritty_warns_about_tabs(self):
        """Test Alacritty warns when tabs config is present."""
        from console_cowboy.ctec.schema import TabBarVisibility, TabConfig

        ctec = CTEC(tabs=TabConfig(visibility=TabBarVisibility.AUTO))
        AlacrittyAdapter.export(ctec)
        assert any("does not support native tabs" in w for w in ctec.warnings)

    def test_alacritty_warns_about_panes(self):
        """Test Alacritty warns when panes config is present."""
        from console_cowboy.ctec.schema import PaneConfig

        ctec = CTEC(panes=PaneConfig(inactive_dim_factor=0.8))
        AlacrittyAdapter.export(ctec)
        assert any("does not support native split panes" in w for w in ctec.warnings)

    def test_alacritty_warns_about_tab_keybindings(self):
        """Test Alacritty warns when tab keybindings are exported."""
        ctec = CTEC(
            key_bindings=[
                KeyBinding(action="new_tab", key="t", mods=["ctrl", "shift"]),
            ]
        )
        AlacrittyAdapter.export(ctec)
        assert any("tab/pane operations" in w.lower() for w in ctec.warnings)

    def test_cross_terminal_tab_conversion(self):
        """Test tab config converts between terminals."""
        # Parse Ghostty config with tabs
        ghostty_config = """
window-show-tab-bar = always
gtk-tabs-location = bottom
window-inherit-working-directory = true
"""
        ctec = GhosttyAdapter.parse("test", content=ghostty_config)

        # Export to Kitty
        kitty_output = KittyAdapter.export(ctec)
        assert "tab_bar_edge bottom" in kitty_output
        assert "tab_bar_min_tabs 1" in kitty_output  # ALWAYS = min_tabs 1

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert "config.tab_bar_at_bottom = true" in wezterm_output

    def test_cross_terminal_pane_conversion(self):
        """Test pane config converts between terminals."""
        # Parse Kitty config with panes
        kitty_config = """
inactive_text_alpha 0.7
active_border_color #00ff00
inactive_border_color #555555
window_border_width 1.5pt
focus_follows_mouse yes
"""
        ctec = KittyAdapter.parse("test", content=kitty_config)

        # Export to Ghostty
        ghostty_output = GhosttyAdapter.export(ctec)
        assert "unfocused-split-opacity = 0.7" in ghostty_output
        assert "focus-follows-mouse = true" in ghostty_output

        # Export to WezTerm
        wezterm_output = WeztermAdapter.export(ctec)
        assert "brightness = 0.7" in wezterm_output
        assert "config.pane_focus_follows_mouse = true" in wezterm_output

    def test_tab_config_roundtrip_ghostty(self):
        """Test tab config roundtrip through Ghostty."""
        from console_cowboy.ctec.schema import (
            NewTabPosition,
            TabBarPosition,
            TabBarVisibility,
            TabConfig,
        )

        original = CTEC(
            tabs=TabConfig(
                visibility=TabBarVisibility.AUTO,
                position=TabBarPosition.TOP,
                new_tab_position=NewTabPosition.END,
                inherit_working_directory=True,
            )
        )
        output = GhosttyAdapter.export(original)
        parsed = GhosttyAdapter.parse("test", content=output)

        assert parsed.tabs.visibility == original.tabs.visibility
        assert parsed.tabs.position == original.tabs.position
        assert parsed.tabs.new_tab_position == original.tabs.new_tab_position
        assert (
            parsed.tabs.inherit_working_directory
            == original.tabs.inherit_working_directory
        )

    def test_pane_config_roundtrip_kitty(self):
        """Test pane config roundtrip through Kitty."""
        from console_cowboy.ctec.schema import PaneConfig

        original = CTEC(
            panes=PaneConfig(
                inactive_dim_factor=0.75,
                focus_follows_mouse=True,
            )
        )
        # Add Kitty-specific border settings via terminal_specific
        original.add_terminal_specific("kitty", "window_border_width", "2.0pt")
        original.add_terminal_specific("kitty", "active_border_color", "#00ff00")
        original.add_terminal_specific("kitty", "inactive_border_color", "#646464")

        output = KittyAdapter.export(original)
        parsed = KittyAdapter.parse("test", content=output)

        # Check common pane settings
        assert parsed.panes.inactive_dim_factor == original.panes.inactive_dim_factor
        assert parsed.panes.focus_follows_mouse == original.panes.focus_follows_mouse
        # Check Kitty-specific settings round-trip via terminal_specific
        assert parsed.get_terminal_specific(
            "kitty", "window_border_width"
        ) == original.get_terminal_specific("kitty", "window_border_width")
        assert parsed.get_terminal_specific(
            "kitty", "active_border_color"
        ) == original.get_terminal_specific("kitty", "active_border_color")
        assert parsed.get_terminal_specific(
            "kitty", "inactive_border_color"
        ) == original.get_terminal_specific("kitty", "inactive_border_color")
