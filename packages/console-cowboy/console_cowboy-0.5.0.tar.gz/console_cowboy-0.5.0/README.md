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
- **Automatic Format Detection**: Detects terminal config formats automatically from file contents
- **Smart Path Resolution**: Use terminal names to read/write to default config locations
- **iTerm2-Color-Schemes Compatible**: Color schemes use the same YAML format as the popular [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes) project
- **Quick Terminal Support**: Migrate quake-style dropdown terminal settings between iTerm2, Ghostty, and Kitty
- **Stdin/Stdout Support**: Pipe configs through shell pipelines
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

### Convert between terminals

```bash
# Convert iTerm2 settings directly to Ghostty config
console-cowboy --from iterm2 --to ghostty

# Convert from a specific file to a terminal's default location
console-cowboy --from ~/path/to/config --to ghostty

# Convert between specific files
console-cowboy --from config.lua --from-type wezterm --to config.toml --to-type alacritty
```

### Export to portable CTEC format

```bash
# Export iTerm2 config to CTEC (outputs to stdout)
console-cowboy --from iterm2

# Export to a file
console-cowboy export --from kitty --to my-config.yaml

# Export a specific iTerm2 profile
console-cowboy export --from iterm2 --profile "Development"
```

### Import from CTEC format

```bash
# Import CTEC to a terminal's default location
console-cowboy import --from my-config.yaml --to ghostty

# Import to a specific file
console-cowboy import --from my-config.yaml --to ~/.config/alacritty/alacritty.toml --to-type alacritty

# Preview import without saving (output to stdout)
console-cowboy import --from my-config.yaml --to-type wezterm
```

### Use with pipes

```bash
# Pipe between commands
console-cowboy --from iterm2 | console-cowboy import --from - --to ghostty

# Read from stdin
cat my-config.yaml | console-cowboy --from - --from-type ctec --to-type kitty
```

## CLI Reference

Console Cowboy uses `--from` and `--to` flags for all operations. The implicit command is conversion; explicit `export`, `import`, and `convert` commands are also available.

### Default Command (Convert)

```bash
console-cowboy [--from SOURCE] [--from-type TYPE] [--to DEST] [--to-type TYPE] [--profile NAME] [--quiet]
```

The `--from` and `--to` arguments accept:
- **Terminal name**: `iterm2`, `ghostty`, `alacritty`, `kitty`, `wezterm`, `vscode`, `terminal_app` - reads from/writes to the terminal's default config location
- **File path**: Path to a config file
- **`-`**: Read from stdin / write to stdout

Type detection:
- If a terminal name is given, that format is used
- If a file path is given, the format is auto-detected from content
- Use `--from-type` or `--to-type` to override: `ctec` or a terminal name

Behavior:
- `--from` without `--to`: Outputs CTEC to stdout
- `--from` with `--to`: Converts and writes to destination
- `--to-type` without `--to`: Outputs that format to stdout

Options:
- `--from`: Source (terminal name, file path, or `-` for stdin)
- `--from-type`: Explicit source type (`ctec` or terminal name)
- `--to`: Destination (terminal name, file path, or `-` for stdout)
- `--to-type`: Explicit destination type (`ctec` or terminal name)
- `--profile`: Profile name (iTerm2/Terminal.app only)
- `--quiet`: Suppress warnings and informational output

### `export`

Export a terminal's configuration to CTEC format (always YAML).

```bash
console-cowboy export --from SOURCE [--from-type TYPE] [--to OUTPUT] [--profile NAME] [--quiet]
```

Options:
- `--from`: Source terminal or config file (required)
- `--from-type`: Explicit source type (terminal name)
- `--to`: Output file (defaults to stdout)
- `--profile`: Profile name (iTerm2/Terminal.app only)
- `--quiet`: Suppress warnings

### `import`

Import a CTEC configuration into a terminal's native format.

```bash
console-cowboy import --from CTEC_FILE [--to DEST] [--to-type TYPE] [--quiet]
```

Options:
- `--from`: CTEC file path or `-` for stdin (required)
- `--to`: Destination terminal or file
- `--to-type`: Explicit destination type (terminal name, required if `--to` is a file)
- `--quiet`: Suppress warnings

### `convert`

Convert directly between terminal configuration formats.

```bash
console-cowboy convert --from SOURCE --to DEST [--from-type TYPE] [--to-type TYPE] [--profile NAME] [--quiet]
```

Options:
- `--from`: Source terminal or config file (required)
- `--to`: Destination terminal or file (required)
- `--from-type`: Explicit source type
- `--to-type`: Explicit destination type
- `--profile`: Profile name (iTerm2/Terminal.app source only)
- `--quiet`: Suppress warnings

### `list`

List all supported terminal emulators.

```bash
console-cowboy list
```

### `info`

Display information about a configuration file.

```bash
console-cowboy info --from SOURCE [--from-type TYPE]
```

## Example Workflows

### Migrate from iTerm2 to Ghostty

```bash
# Direct conversion to Ghostty's default config location
console-cowboy --from iterm2 --to ghostty
```

### Backup your terminal config

```bash
# Export to a portable format
console-cowboy export --from ghostty --to ~/backups/terminal-config.yaml
```

### Test a config on another terminal

```bash
# Preview how your config would look in Kitty
console-cowboy --from ~/.config/alacritty/alacritty.toml --to-type kitty

# Or pipe it for processing
console-cowboy --from wezterm | less
```

### Use in scripts

```bash
# Convert multiple terminals in a script
for terminal in ghostty alacritty kitty; do
  console-cowboy --from iterm2 --to-type $terminal > ~/configs/$terminal-config
done
```

## CTEC Format

The Common Terminal Emulator Configuration (CTEC) format is a portable YAML representation of terminal settings. It captures:

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
