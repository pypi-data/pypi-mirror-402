"""Tests for the terminal registry."""

from console_cowboy.terminals import (
    GhosttyAdapter,
    HyperAdapter,
    ITerm2Adapter,
    TerminalAppAdapter,
    TerminalRegistry,
    VSCodeAdapter,
)


class TestTerminalRegistry:
    """Tests for the terminal registry."""

    def test_get_all_terminals(self):
        names = TerminalRegistry.get_names()
        assert "iterm2" in names
        assert "ghostty" in names
        assert "alacritty" in names
        assert "kitty" in names
        assert "wezterm" in names
        assert "vscode" in names
        assert "terminal_app" in names
        assert "hyper" in names

    def test_get_terminal_by_name(self):
        adapter = TerminalRegistry.get("ghostty")
        assert adapter == GhosttyAdapter

    def test_get_terminal_case_insensitive(self):
        adapter = TerminalRegistry.get("GHOSTTY")
        assert adapter == GhosttyAdapter

    def test_get_unknown_terminal(self):
        adapter = TerminalRegistry.get("unknown")
        assert adapter is None

    def test_list_terminals(self):
        terminals = TerminalRegistry.list_terminals()
        assert len(terminals) == 8
        assert ITerm2Adapter in terminals
        assert VSCodeAdapter in terminals
        assert TerminalAppAdapter in terminals
        assert HyperAdapter in terminals
