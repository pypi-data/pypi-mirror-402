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
    def can_parse(cls, content: str) -> bool:
        """
        Check if this adapter can likely parse the given content.

        Override this in subclasses to provide format detection.
        Returns True if the content looks like this terminal's config format.

        Args:
            content: The file content to check

        Returns:
            True if this adapter can likely parse the content
        """
        return False

    @classmethod
    def get_default_config_path_for_platform(cls) -> Path | None:
        """
        Get the default configuration file path for this terminal on the current platform.

        This returns the expected path even if the file doesn't exist,
        which is useful for writing new config files.

        Returns:
            Path to the default config location, or None if not applicable
        """
        if not cls.default_config_paths:
            return None

        home = Path.home()
        # Return the first path (preferred location) even if it doesn't exist
        return home / cls.default_config_paths[0]

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

    @classmethod
    def detect_terminal_type(cls, content: str) -> type[TerminalAdapter] | None:
        """
        Detect which terminal adapter can parse the given content.

        Tries each registered adapter's can_parse method to find a match.

        Args:
            content: The file content to check

        Returns:
            The adapter class that can parse this content, or None if no match
        """
        for adapter in cls._adapters.values():
            if adapter.can_parse(content):
                return adapter
        return None

    @classmethod
    def detect_from_file(cls, path: Path) -> type[TerminalAdapter] | None:
        """
        Detect which terminal adapter can parse a file.

        First checks file extension hints, then content detection.

        Args:
            path: Path to the file to check

        Returns:
            The adapter class that can parse this file, or None if no match
        """
        if not path.exists():
            return None

        content = path.read_text()
        return cls.detect_terminal_type(content)

    @classmethod
    def is_ctec_file(cls, content: str) -> bool:
        """
        Check if the content appears to be a CTEC configuration file.

        Args:
            content: The file content to check

        Returns:
            True if the content looks like CTEC format
        """
        # CTEC files are YAML with a version field
        import yaml

        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                # CTEC must have a version field
                if "version" in data:
                    # And typically has ctec-specific fields
                    ctec_fields = {
                        "source_terminal",
                        "color_scheme",
                        "font",
                        "cursor",
                        "window",
                        "behavior",
                        "scroll",
                        "key_bindings",
                        "terminal_specific",
                    }
                    return bool(ctec_fields & set(data.keys()))
        except Exception:
            pass
        return False

    @classmethod
    def get_default_config_path(cls, terminal_name: str) -> Path | None:
        """
        Get the default config path for a terminal that exists on disk.

        Args:
            terminal_name: The terminal name (e.g., 'ghostty', 'iterm2')

        Returns:
            Path to the existing config file, or None if not found
        """
        adapter = cls.get(terminal_name)
        if adapter:
            return adapter.get_default_config_path()
        return None

    @classmethod
    def get_default_config_path_for_write(cls, terminal_name: str) -> Path | None:
        """
        Get the default config path for writing to a terminal.

        Returns the expected location even if it doesn't exist yet.

        Args:
            terminal_name: The terminal name (e.g., 'ghostty', 'iterm2')

        Returns:
            Path to the config location, or None if not applicable
        """
        adapter = cls.get(terminal_name)
        if adapter:
            return adapter.get_default_config_path_for_platform()
        return None
