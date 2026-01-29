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
- **Multiple Output Formats**: CTEC files can be stored as TOML (default), JSON, or YAML
- **Incompatibility Reporting**: Clearly reports which settings cannot be converted between terminals
- **Terminal-Specific Settings**: Preserves terminal-specific settings that don't have equivalents in other terminals

## Installation

Install using `pip`:

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
# Export Ghostty config to CTEC format
console-cowboy export ghostty -o my-config.toml

# Export iTerm2 config
console-cowboy export iterm2 -o my-config.toml

# Export to JSON format
console-cowboy export kitty -o my-config.json -f json
```

### Import into a different terminal

```bash
# Import CTEC config into Alacritty format
console-cowboy import my-config.toml -t alacritty -o ~/.config/alacritty/alacritty.toml

# Import into Wezterm
console-cowboy import my-config.toml -t wezterm -o ~/.wezterm.lua

# Preview output without saving
console-cowboy import my-config.toml -t ghostty
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
console-cowboy export TERMINAL [-i INPUT] [-o OUTPUT] [-f FORMAT] [-q]
```

Options:
- `TERMINAL`: Source terminal (iterm2, ghostty, alacritty, kitty, wezterm)
- `-i, --input`: Input config file (defaults to terminal's standard location)
- `-o, --output`: Output file (defaults to stdout)
- `-f, --format`: Output format: toml, json, yaml (default: toml)
- `-q, --quiet`: Suppress warnings and informational output

### `import`

Import a CTEC configuration into a terminal's native format.

```bash
console-cowboy import INPUT_FILE -t TERMINAL [-o OUTPUT] [-f FORMAT] [-q]
```

Options:
- `INPUT_FILE`: Path to CTEC configuration file
- `-t, --terminal`: Target terminal (required)
- `-o, --output`: Output file (defaults to stdout)
- `-f, --format`: Input format override (auto-detected from extension)
- `-q, --quiet`: Suppress warnings

### `convert`

Convert directly between terminal configuration formats.

```bash
console-cowboy convert INPUT_FILE -f FROM_TERMINAL -t TO_TERMINAL [-o OUTPUT] [-q]
```

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

```toml
version = "1.0"
source_terminal = "ghostty"

[color_scheme]
name = "Tomorrow Night"

[color_scheme.foreground]
r = 197
g = 200
b = 198

[color_scheme.background]
r = 29
g = 31
b = 33

[font]
family = "JetBrains Mono"
size = 14.0
ligatures = true

[cursor]
style = "block"
blink = true
blink_interval = 500

[window]
columns = 120
rows = 40
opacity = 0.95

[behavior]
shell = "/bin/zsh"
scrollback_lines = 10000
bell_mode = "visual"

[[key_bindings]]
action = "Copy"
key = "c"
mods = ["ctrl", "shift"]
```

## Supported Terminals

| Terminal | Config Format | Import | Export |
|----------|--------------|--------|--------|
| iTerm2 | plist XML | Yes | Yes |
| Ghostty | key=value | Yes | Yes |
| Alacritty | TOML/YAML | Yes | Yes |
| Kitty | key value | Yes | Yes |
| Wezterm | Lua | Yes | Yes |
| Terminal.app | plist XML | Yes | Yes |

### Default Config Locations

- **iTerm2**: `~/Library/Preferences/com.googlecode.iterm2.plist`
- **Ghostty**: `~/.config/ghostty/config`
- **Alacritty**: `~/.config/alacritty/alacritty.toml` or `.yml`
- **Kitty**: `~/.config/kitty/kitty.conf`
- **Wezterm**: `~/.wezterm.lua` or `~/.config/wezterm/wezterm.lua`
- **Terminal.app**: `~/Library/Preferences/com.apple.Terminal.plist`

## Compatibility Notes

Not all settings can be perfectly converted between terminals:

1. **Color Formats**: All terminals use slightly different color representations. Console Cowboy normalizes to RGB and converts appropriately.

2. **Font Handling**: Font names may need adjustment depending on how each terminal resolves fonts.

3. **Key Bindings**: Different terminals have different action names and modifier key representations. Key bindings are converted on a best-effort basis.

4. **Wezterm Lua**: Wezterm uses Lua for configuration. Console Cowboy can parse common patterns but complex Lua configurations may not be fully captured.

5. **Terminal-Specific Features**: Features unique to one terminal (like iTerm2's "Unlimited Scrollback" or Kitty's remote control) are preserved but only work when converting back to the same terminal.

6. **Terminal.app NSKeyedArchiver**: Terminal.app uses Apple's NSKeyedArchiver format for colors and fonts. Console Cowboy can parse this format, but for best accuracy on macOS, installing PyObjC (`pip install pyobjc-framework-Cocoa`) is recommended.

Console Cowboy will report any incompatibilities or settings that couldn't be converted.

## Development

To contribute to this tool, first checkout the code:

```bash
git clone https://github.com/zetlen/console-cowboy
cd console-cowboy
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -e '.[test]'
```

Run the tests:

```bash
python -m pytest
```

Run tests with coverage:

```bash
python -m pytest --cov=console_cowboy
```

## License

Apache 2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Adding Support for New Terminals

1. Create a new adapter in `console_cowboy/terminals/`
2. Inherit from `TerminalAdapter`
3. Implement `parse()` and `export()` methods
4. Register the adapter in `console_cowboy/terminals/__init__.py`
5. Add test fixtures and tests
