# console-cowboy

[![PyPI](https://img.shields.io/pypi/v/console-cowboy.svg)](https://pypi.org/project/console-cowboy/)
[![Changelog](https://img.shields.io/github/v/release/zetlen/console-cowboy?include_prereleases&label=changelog)](https://github.com/zetlen/console-cowboy/releases)
[![Tests](https://github.com/zetlen/console-cowboy/actions/workflows/test.yml/badge.svg)](https://github.com/zetlen/console-cowboy/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zetlen/console-cowboy/blob/master/LICENSE)

**Hop terminals like you hop Linux distributions.**

Console Cowboy is a CLI tool for making terminal configurations portable across different terminal emulators. Export your settings from one terminal and import them into another.

## Features

- **Portable Configuration Format**: Uses CTEC (Common Terminal Emulator Configuration) as an intermediate representation
- **Multiple Terminal Support**: Import and export configurations for:
  - iTerm2
  - Ghostty
  - Alacritty
  - Kitty
  - Wezterm
  - Terminal.app (macOS)
  - VS Code (integrated terminal)
- **iTerm2-Color-Schemes Compatible**: Color schemes use the same YAML format as the popular [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes) project
- **Quick Terminal Support**: Migrate quake-style dropdown terminal settings between iTerm2, Ghostty, and Kitty
- **Output Formats**: CTEC files can be stored as YAML (default) or JSON
- **Incompatibility Reporting**: Clearly reports which settings cannot be converted between terminals
- **Terminal-Specific Settings**: Preserves terminal-specific settings that don't have equivalents in other terminals

## Installation

Install using `uv` (recommended):

```bash
uv tool install console-cowboy
```

Or with `pip`:

```bash
pip install console-cowboy
```

Or with `pipx` for isolated installation:

```bash
pipx install console-cowboy
```

## Quick Start

### Export your current terminal config

```bash
# Export Ghostty config to CTEC format (YAML by default)
console-cowboy export ghostty -o my-config.yaml

# Export iTerm2 config
console-cowboy export iterm2 -o my-config.yaml

# Export to JSON format
console-cowboy export kitty -o my-config.json -f json
```

### Import into a different terminal

```bash
# Import CTEC config into Alacritty format
console-cowboy import my-config.yaml -t alacritty -o ~/.config/alacritty/alacritty.toml

# Import into Wezterm
console-cowboy import my-config.yaml -t wezterm -o ~/.wezterm.lua

# Preview output without saving
console-cowboy import my-config.yaml -t ghostty
```

### Convert directly between terminals

```bash
# Convert Kitty config to Ghostty
console-cowboy convert ~/.config/kitty/kitty.conf -f kitty -t ghostty -o ~/.config/ghostty/config

# Convert iTerm2 to Alacritty
console-cowboy convert ~/Library/Preferences/com.googlecode.iterm2.plist -f iterm2 -t alacritty
```

## Commands

### `export`

Export a terminal's configuration to CTEC format.

```bash
console-cowboy export TERMINAL [-i INPUT] [-o OUTPUT] [-f FORMAT] [-p PROFILE] [-q]
```

Options:
- `TERMINAL`: Source terminal (iterm2, ghostty, alacritty, kitty, wezterm, vscode, terminal_app)
- `-i, --input`: Input config file (defaults to terminal's standard location)
- `-o, --output`: Output file (defaults to stdout)
- `-f, --format`: Output format: yaml, json (default: yaml)
- `-p, --profile`: Profile name to export (iTerm2 and Terminal.app only)
- `-q, --quiet`: Suppress warnings and informational output

### `import`

Import a CTEC configuration into a terminal's native format.

```bash
console-cowboy import INPUT_FILE -t TERMINAL [-o OUTPUT] [-f FORMAT] [-q]
```

Options:
- `INPUT_FILE`: Path to CTEC configuration file (.yaml or .json)
- `-t, --terminal`: Target terminal (required)
- `-o, --output`: Output file (defaults to stdout)
- `-f, --format`: Input format override (auto-detected from extension)
- `-q, --quiet`: Suppress warnings

### `convert`

Convert directly between terminal configuration formats.

```bash
console-cowboy convert INPUT_FILE -f FROM_TERMINAL -t TO_TERMINAL [-o OUTPUT] [-p PROFILE] [-q]
```

Options:
- `INPUT_FILE`: Path to source terminal configuration file
- `-f, --from`: Source terminal (required)
- `-t, --to`: Target terminal (required)
- `-o, --output`: Output file (defaults to stdout)
- `-p, --profile`: Profile name to convert (iTerm2 and Terminal.app source only)
- `-q, --quiet`: Suppress warnings

### `list`

List all supported terminal emulators.

```bash
console-cowboy list
```

### `info`

Display information about a configuration file.

```bash
console-cowboy info INPUT_FILE [-t TERMINAL]
```

## CTEC Format

The Common Terminal Emulator Configuration (CTEC) format is a portable representation of terminal settings. It captures:

### Color Scheme
- Foreground and background colors
- Cursor and selection colors
- Full 16-color ANSI palette (normal and bright variants)

### Font Configuration
- Font family, size, and line height
- Bold and italic font variants
- Ligature support

### Cursor Configuration
- Style (block, beam, underline)
- Blink behavior and interval

### Window Configuration
- Initial dimensions (columns/rows)
- Opacity and blur effects
- Padding and decorations
- Startup mode

### Behavior Configuration
- Default shell
- Scrollback buffer size
- Bell mode (audible, visual, none)
- Copy-on-select behavior

### Key Bindings
- Keyboard shortcuts with modifiers

### Terminal-Specific Settings
Settings that cannot be mapped to common CTEC fields are preserved in a `terminal_specific` section, allowing them to be restored when converting back to the same terminal.

### Example CTEC File

```yaml
version: "1.0"
source_terminal: ghostty

color_scheme:
  name: Tomorrow Night
  foreground: "#c5c8c6"
  background: "#1d1f21"
  cursor: "#c5c8c6"
  black: "#1d1f21"
  red: "#cc6666"
  green: "#b5bd68"
  yellow: "#f0c674"
  blue: "#81a2be"
  magenta: "#b294bb"
  cyan: "#8abeb7"
  white: "#c5c8c6"

font:
  family: JetBrains Mono
  size: 14.0
  ligatures: true

cursor:
  style: block
  blink: true
  blink_interval: 500

window:
  columns: 120
  rows: 40
  opacity: 0.95

behavior:
  shell: /bin/zsh
  bell_mode: visual

scroll:
  lines: 10000

key_bindings:
  - action: Copy
    key: c
    mods:
      - ctrl
      - shift
```

## Supported Terminals

| Terminal | Config Format | Import | Export | Quick Terminal |
|----------|--------------|--------|--------|----------------|
| iTerm2 | plist XML | Yes | Yes | Yes |
| Ghostty | key=value | Yes | Yes | Yes |
| Alacritty | TOML/YAML | Yes | Yes | No |
| Kitty | key value | Yes | Yes | Yes |
| Wezterm | Lua | Yes | Yes | No |
| VS Code | JSON | Yes | Yes | No |
| Terminal.app | plist XML | Yes | Yes | No |

### Default Config Locations

- **iTerm2**: `~/Library/Preferences/com.googlecode.iterm2.plist`
- **Ghostty**: `~/.config/ghostty/config`
- **Alacritty**: `~/.config/alacritty/alacritty.toml` or `.yml`
- **Kitty**: `~/.config/kitty/kitty.conf`
- **Wezterm**: `~/.wezterm.lua` or `~/.config/wezterm/wezterm.lua`
- **VS Code**: `~/Library/Application Support/Code/User/settings.json` (macOS) or `~/.config/Code/User/settings.json` (Linux)
- **Terminal.app**: `~/Library/Preferences/com.apple.Terminal.plist`

## Compatibility Notes

Not all settings can be perfectly converted between terminals:

1. **Color Formats**: All terminals use slightly different color representations. Console Cowboy normalizes to hex colors (e.g., `#c5c8c6`) compatible with the iTerm2-Color-Schemes format.

2. **Font Handling**: Font names may need adjustment depending on how each terminal resolves fonts.

3. **Key Bindings**: Different terminals have different action names and modifier key representations. Key bindings are converted on a best-effort basis.

4. **Wezterm Lua**: Wezterm uses Lua for configuration. Console Cowboy can parse common patterns but complex Lua configurations may not be fully captured.

5. **Terminal-Specific Features**: Features unique to one terminal (like iTerm2's "Unlimited Scrollback" or Kitty's remote control) are preserved but only work when converting back to the same terminal.

6. **Terminal.app NSKeyedArchiver**: Terminal.app uses Apple's NSKeyedArchiver format for colors and fonts. Console Cowboy can parse this format, but for best accuracy on macOS, installing PyObjC (`uv pip install pyobjc-framework-Cocoa`) is recommended.

7. **Quick Terminal / Hotkey Window**: Quake-style dropdown terminal settings can be migrated between iTerm2, Ghostty, and Kitty. Alacritty, Wezterm, and VS Code don't have native quick terminal support.

8. **VS Code**: VS Code's integrated terminal has limited customization compared to dedicated terminal emulators. Only colors, fonts, cursor, and basic behavior settings are supported.

Console Cowboy will report any incompatibilities or settings that couldn't be converted.

## Development

To contribute to this tool, first checkout the code:

```bash
git clone https://github.com/zetlen/console-cowboy
cd console-cowboy
```

Install dependencies with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync --all-extras
```

Run the tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=console_cowboy
```

Run the CLI during development:

```bash
uv run console-cowboy --help
```

## License

Apache 2.0

## Contributing

Contributions are welcome! Repo's open.

### Adding Support for New Terminals

1. Create a new adapter in `console_cowboy/terminals/`
2. Inherit from `TerminalAdapter`
3. Implement `parse()` and `export()` methods
4. Register the adapter in `console_cowboy/terminals/__init__.py`
5. Add test fixtures and tests
