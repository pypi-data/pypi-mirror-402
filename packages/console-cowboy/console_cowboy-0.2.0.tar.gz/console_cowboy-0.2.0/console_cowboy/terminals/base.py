"""
Base classes for terminal emulator adapters.

Each terminal emulator adapter inherits from TerminalAdapter and implements
methods to parse (import) and export configurations to/from CTEC format.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from console_cowboy.ctec.schema import CTEC


class TerminalAdapter(ABC):
    """
    Abstract base class for terminal emulator configuration adapters.

    Each terminal emulator implementation should inherit from this class
    and provide methods to:
    - Parse the terminal's native config format into CTEC
    - Export CTEC to the terminal's native config format
    """

    # Terminal identifier (lowercase, e.g., 'iterm2', 'ghostty')
    name: str = ""

    # Human-readable terminal name
    display_name: str = ""

    # Description of the terminal
    description: str = ""

    # File extensions for config files
    config_extensions: list[str] = []

    # Default config file paths (relative to home directory)
    default_config_paths: list[str] = []

    @classmethod
    @abstractmethod
    def parse(
        cls,
        source: str | Path,
        *,
        content: str | None = None,
    ) -> CTEC:
        """
        Parse a terminal configuration file into CTEC format.

        Args:
            source: Path to the configuration file, or identifier for content
            content: Optional string content (if provided, source is used as identifier)

        Returns:
            CTEC configuration

        Raises:
            FileNotFoundError: If the source file doesn't exist
            ValueError: If the configuration cannot be parsed
        """
        pass

    @classmethod
    @abstractmethod
    def export(cls, ctec: CTEC) -> str:
        """
        Export CTEC configuration to the terminal's native format.

        Args:
            ctec: CTEC configuration to export

        Returns:
            String in the terminal's native configuration format
        """
        pass

    @classmethod
    def get_default_config_path(cls) -> Path | None:
        """
        Get the default configuration file path for this terminal.

        Returns:
            Path to the default config file, or None if not found
        """
        home = Path.home()
        for path in cls.default_config_paths:
            full_path = home / path
            if full_path.exists():
                return full_path
        return None

    @classmethod
    def write_config(cls, ctec: CTEC, path: str | Path) -> None:
        """
        Export and write CTEC configuration to a file.

        Args:
            ctec: CTEC configuration to export
            path: Path to write the configuration to
        """
        content = cls.export(ctec)
        Path(path).write_text(content)


class TerminalRegistry:
    """
    Registry of available terminal adapters.
    """

    _adapters: dict[str, type[TerminalAdapter]] = {}

    @classmethod
    def register(cls, adapter: type[TerminalAdapter]) -> None:
        """
        Register a terminal adapter.

        Args:
            adapter: Terminal adapter class to register
        """
        cls._adapters[adapter.name] = adapter

    @classmethod
    def get(cls, name: str) -> type[TerminalAdapter] | None:
        """
        Get a terminal adapter by name.

        Args:
            name: Terminal name (case-insensitive)

        Returns:
            Terminal adapter class, or None if not found
        """
        return cls._adapters.get(name.lower())

    @classmethod
    def list_terminals(cls) -> list[type[TerminalAdapter]]:
        """
        List all registered terminal adapters.

        Returns:
            List of terminal adapter classes
        """
        return list(cls._adapters.values())

    @classmethod
    def get_names(cls) -> list[str]:
        """
        Get names of all registered terminals.

        Returns:
            List of terminal names
        """
        return list(cls._adapters.keys())
