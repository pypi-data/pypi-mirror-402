"""
Terminal emulator parsers and exporters.

This module provides classes for reading and writing configuration files
for various terminal emulators.
"""

from .alacritty import AlacrittyAdapter
from .base import TerminalAdapter, TerminalRegistry
from .ghostty import GhosttyAdapter
from .hyper import HyperAdapter
from .iterm2 import ITerm2Adapter
from .kitty import KittyAdapter
from .terminal_app import TerminalAppAdapter
from .vscode import VSCodeAdapter
from .wezterm import WeztermAdapter

# Register all adapters
TerminalRegistry.register(ITerm2Adapter)
TerminalRegistry.register(GhosttyAdapter)
TerminalRegistry.register(AlacrittyAdapter)
TerminalRegistry.register(KittyAdapter)
TerminalRegistry.register(WeztermAdapter)
TerminalRegistry.register(VSCodeAdapter)
TerminalRegistry.register(TerminalAppAdapter)
TerminalRegistry.register(HyperAdapter)

__all__ = [
    "TerminalAdapter",
    "TerminalRegistry",
    "ITerm2Adapter",
    "GhosttyAdapter",
    "AlacrittyAdapter",
    "KittyAdapter",
    "WeztermAdapter",
    "VSCodeAdapter",
    "TerminalAppAdapter",
    "HyperAdapter",
]
