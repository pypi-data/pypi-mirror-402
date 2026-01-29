"""
Lua runtime support for parsing WezTerm configuration files.

This module uses lupa to embed a Lua interpreter and execute WezTerm
config files with a mock wezterm module that captures all configuration
settings.
"""

from dataclasses import dataclass, field
from typing import Any

from lupa import LuaRuntime  # type: ignore[import-untyped]


@dataclass
class FontSpec:
    """Captured font specification from wezterm.font() or font_with_fallback()."""

    family: str | None = None
    weight: str | None = None
    style: str | None = None
    fallbacks: list[str] = field(default_factory=list)
    # HarfBuzz features like {'calt=0', 'liga=0'}
    harfbuzz_features: list[str] = field(default_factory=list)
    # FreeType settings
    freetype_load_target: str | None = None
    freetype_render_target: str | None = None

    def __repr__(self) -> str:
        return f"FontSpec(family={self.family!r}, weight={self.weight!r}, fallbacks={self.fallbacks!r})"


@dataclass
class ActionSpec:
    """Captured action specification from wezterm.action.*."""

    name: str
    args: tuple[Any, ...] = field(default_factory=tuple)

    def __repr__(self) -> str:
        return f"ActionSpec({self.name!r}, args={self.args!r})"


@dataclass
class EventCallback:
    """Captured wezterm.on() event callback."""

    event_name: str
    # We can't preserve the actual function, but we note it exists
    has_callback: bool = True

    def __repr__(self) -> str:
        return f"EventCallback({self.event_name!r})"


class MockWeztermAction:
    """
    Mock for wezterm.action namespace.

    Captures action calls like wezterm.action.CopyTo("Clipboard").
    """

    def __getattr__(self, name: str):
        """Return a callable that creates ActionSpec for any action name."""

        def action_factory(*args: Any) -> ActionSpec:
            return ActionSpec(name=name, args=args)

        return action_factory

    def __getitem__(self, name: str):
        """Support Lua-style indexing (action[name])."""
        return self.__getattr__(name)


class MockWeztermColor:
    """Mock for wezterm.color namespace."""

    def parse(self, color_str: str) -> str:
        """Return the color string unchanged - just a passthrough."""
        return color_str

    def get_builtin_schemes(self) -> dict:
        """Return empty dict - we don't have access to actual schemes."""
        return {}


class ConfigCapture(dict):
    """
    A dict subclass that captures all config assignments.

    Acts like a Lua table but is a Python dict for easy access.
    """

    pass


class MockWezterm:
    """
    Mock wezterm module that captures configuration calls.

    Provides the same API as the real wezterm module but captures
    all calls for later extraction.
    """

    def __init__(self) -> None:
        self.action = MockWeztermAction()
        self.color = MockWeztermColor()
        self._font_calls: list[FontSpec] = []
        self._event_callbacks: list[EventCallback] = []

    def config_builder(self) -> ConfigCapture:
        """Return a config object that captures all assignments."""
        return ConfigCapture()

    def font(self, family: str, opts: dict | None = None) -> FontSpec:
        """Capture a font() call."""
        spec = FontSpec(family=family)
        if opts:
            # opts is a Lua table, convert to dict if needed
            opts_dict = _lua_value_to_python(opts) if hasattr(opts, "items") else opts
            if isinstance(opts_dict, dict):
                spec.weight = opts_dict.get("weight")
                spec.style = opts_dict.get("style")
                # Capture HarfBuzz features
                hb = opts_dict.get("harfbuzz_features")
                if hb:
                    if isinstance(hb, (list, tuple)):
                        spec.harfbuzz_features = list(hb)
                    elif isinstance(hb, dict):
                        # Lua table with numeric keys
                        spec.harfbuzz_features = list(hb.values())
                # Capture FreeType settings
                spec.freetype_load_target = opts_dict.get("freetype_load_target")
                spec.freetype_render_target = opts_dict.get("freetype_render_target")
        self._font_calls.append(spec)
        return spec

    def font_with_fallback(self, fonts: Any) -> FontSpec:
        """Capture a font_with_fallback() call."""
        spec = FontSpec()

        # Convert Lua table to Python list
        font_list = _lua_table_to_list(fonts)

        for i, font_entry in enumerate(font_list):
            if isinstance(font_entry, dict):
                # Table entry like { family = "Name", weight = "Bold" }
                if i == 0:
                    spec.family = font_entry.get("family")
                    spec.weight = font_entry.get("weight")
                    spec.style = font_entry.get("style")
                    # Capture HarfBuzz features from primary font
                    hb = font_entry.get("harfbuzz_features")
                    if hb:
                        if isinstance(hb, (list, tuple)):
                            spec.harfbuzz_features = list(hb)
                        elif isinstance(hb, dict):
                            spec.harfbuzz_features = list(hb.values())
                    spec.freetype_load_target = font_entry.get("freetype_load_target")
                    spec.freetype_render_target = font_entry.get(
                        "freetype_render_target"
                    )
                else:
                    # Fallback with weight - just use the family name
                    if font_entry.get("family"):
                        spec.fallbacks.append(font_entry["family"])
            elif isinstance(font_entry, str):
                # Simple string entry
                if i == 0:
                    spec.family = font_entry
                else:
                    spec.fallbacks.append(font_entry)

        self._font_calls.append(spec)
        return spec

    def default_hyperlink_rules(self) -> list:
        """Return an empty list that rules can be inserted into."""
        return []

    def on(self, event_name: str, callback: Any = None) -> None:
        """Capture wezterm.on() event registration."""
        self._event_callbacks.append(EventCallback(event_name=event_name))

    def get_builtin_color_schemes(self) -> dict:
        """Return empty dict - we don't have access to actual schemes."""
        return {}


def _lua_table_to_list(lua_table: Any) -> list:
    """Convert a Lua table (with numeric keys) to a Python list."""
    if isinstance(lua_table, (list, tuple)):
        return [_lua_value_to_python(v) for v in lua_table]

    # Try to iterate over numeric keys starting at 1 (Lua convention)
    result = []
    try:
        i = 1
        while True:
            val = lua_table[i]
            if val is None:
                break
            result.append(_lua_value_to_python(val))
            i += 1
    except (KeyError, TypeError, IndexError):
        pass

    return result


def _lua_value_to_python(value: Any) -> Any:
    """Recursively convert Lua values to Python equivalents."""
    if value is None:
        return None

    # Check for lupa table type
    if hasattr(value, "items"):
        # Check if it's array-like (consecutive integer keys starting at 1)
        is_array = True
        max_key = 0
        for k in value.keys():
            if isinstance(k, int) and k > 0:
                max_key = max(max_key, k)
            else:
                is_array = False
                break

        if is_array and max_key > 0:
            # Check consecutive
            try:
                for i in range(1, max_key + 1):
                    _ = value[i]
            except (KeyError, TypeError):
                is_array = False

        if is_array and max_key > 0:
            return [_lua_value_to_python(value[i]) for i in range(1, max_key + 1)]
        else:
            return {
                _lua_value_to_python(k): _lua_value_to_python(v)
                for k, v in value.items()
            }

    # Handle our custom types
    if isinstance(value, (FontSpec, ActionSpec, EventCallback)):
        return value

    # Primitives
    return value


def _lua_table_to_dict(lua_table: Any) -> dict:
    """Convert a Lua table to a Python dict, recursively."""
    if isinstance(lua_table, dict):
        return lua_table

    result = {}
    if hasattr(lua_table, "items"):
        for k, v in lua_table.items():
            result[k] = _lua_value_to_python(v)
    return result


def _deep_convert_lua_values(value: Any) -> Any:
    """Recursively convert all Lua tables in a value to Python types."""
    if value is None:
        return None

    # Check for lupa table type
    if hasattr(value, "items") and hasattr(value, "keys"):
        # Check if it's array-like (consecutive integer keys starting at 1)
        keys = list(value.keys())
        int_keys = [k for k in keys if isinstance(k, int) and k > 0]

        if int_keys and len(int_keys) == len(keys):
            # Check if consecutive from 1
            max_key = max(int_keys)
            if set(int_keys) == set(range(1, max_key + 1)):
                # It's an array
                return [
                    _deep_convert_lua_values(value[i]) for i in range(1, max_key + 1)
                ]

        # It's a dict
        return {k: _deep_convert_lua_values(v) for k, v in value.items()}

    # Handle our custom types - keep them as-is
    if isinstance(value, (FontSpec, ActionSpec, EventCallback)):
        return value

    # Handle Python dicts (shouldn't happen but be safe)
    if isinstance(value, dict):
        return {k: _deep_convert_lua_values(v) for k, v in value.items()}

    # Handle Python lists
    if isinstance(value, (list, tuple)):
        return [_deep_convert_lua_values(item) for item in value]

    # Primitives
    return value


@dataclass
class WeztermConfigResult:
    """Result of executing a WezTerm config, with metadata."""

    config: dict
    event_callbacks: list[EventCallback]


def execute_wezterm_config(lua_source: str) -> dict[str, Any]:
    """
    Execute a WezTerm Lua config and return the captured configuration.

    The Lua environment is sandboxed to prevent arbitrary code execution.
    Only safe standard library functions are available (string, table, math),
    and dangerous functions (os.execute, io.*, loadfile, etc.) are blocked.

    Args:
        lua_source: The Lua source code to execute

    Returns:
        A dict containing all captured config values, plus special keys:
        - '_wezterm_events': List of EventCallback for wezterm.on() calls

    Raises:
        ValueError: If the Lua code fails to execute or doesn't return config
    """
    lua = LuaRuntime(unpack_returned_tuples=True)

    # Create our mock wezterm module
    mock_wezterm = MockWezterm()

    # Set up the Lua environment with our mock
    lua.globals()["_mock_wezterm"] = mock_wezterm
    lua.globals()["_user_code"] = lua_source

    # Create the wezterm module and sandboxed environment in Lua
    # Uses load() with env parameter (Lua 5.2+) to restrict the user code's environment
    setup_and_execute_code = """
    local _mock = _mock_wezterm
    local _user_code = _user_code

    -- Create the wezterm module table
    local wezterm = {}

    -- config_builder returns a table that we can use
    function wezterm.config_builder()
        return _mock:config_builder()
    end

    -- font captures font settings
    function wezterm.font(family, opts)
        return _mock:font(family, opts)
    end

    -- font_with_fallback captures fallback fonts
    function wezterm.font_with_fallback(fonts)
        return _mock:font_with_fallback(fonts)
    end

    -- default_hyperlink_rules returns a list
    function wezterm.default_hyperlink_rules()
        return _mock:default_hyperlink_rules()
    end

    -- on() captures event callbacks
    function wezterm.on(event_name, callback)
        _mock:on(event_name, callback)
    end

    -- get_builtin_color_schemes returns empty (we don't have real schemes)
    function wezterm.get_builtin_color_schemes()
        return _mock:get_builtin_color_schemes()
    end

    -- color namespace
    wezterm.color = {
        parse = function(color_str)
            return _mock.color:parse(color_str)
        end,
        get_builtin_schemes = function()
            return _mock.color:get_builtin_schemes()
        end
    }

    -- Create the action namespace with a metatable for dynamic access
    wezterm.action = setmetatable({}, {
        __index = function(_, name)
            -- Return a function that creates an action
            return function(...)
                return _mock.action[name](...)
            end
        end
    })

    -- Provide nop for target_triple (platform detection)
    wezterm.target_triple = "unknown-unknown-unknown"

    -- Create a sandboxed environment with only safe globals
    -- This prevents malicious configs from executing system commands
    local safe_env = {
        -- Safe standard functions
        assert = assert,
        error = error,
        ipairs = ipairs,
        next = next,
        pairs = pairs,
        pcall = pcall,
        rawequal = rawequal,
        rawget = rawget,
        rawset = rawset,
        select = select,
        setmetatable = setmetatable,
        getmetatable = getmetatable,
        tonumber = tonumber,
        tostring = tostring,
        type = type,
        xpcall = xpcall,

        -- Safe standard libraries (pure functions, no I/O)
        string = string,
        table = table,
        math = math,

        -- Version info
        _VERSION = _VERSION,

        -- Our mock wezterm module
        wezterm = wezterm,

        -- Sandboxed require that only returns wezterm
        require = function(name)
            if name == "wezterm" then
                return wezterm
            end
            error("require('" .. name .. "') is not available in sandboxed environment", 2)
        end,

        -- Sandboxed print (no-op, but some configs may call it)
        print = function() end,
    }

    -- Allow safe_env to reference itself as _G
    safe_env._G = safe_env

    -- Load the user's config as a function with sandboxed environment
    -- In Lua 5.2+, load() takes the environment as the 4th parameter
    local user_func, err = load(_user_code, "wezterm.lua", "t", safe_env)
    if not user_func then
        error("Failed to parse WezTerm config: " .. (err or "unknown error"))
    end

    -- Execute and return the result
    return user_func()
    """

    try:
        result = lua.execute(setup_and_execute_code)
    except Exception as e:
        raise ValueError(f"Failed to execute WezTerm config: {e}") from e

    # The result should be the config table (from 'return config')
    if result is None:
        raise ValueError("WezTerm config did not return a config table")

    # Convert all Lua tables to Python dicts/lists
    config_dict = _deep_convert_lua_values(result)

    # Add captured event callbacks as special key
    if mock_wezterm._event_callbacks:
        config_dict["_wezterm_events"] = mock_wezterm._event_callbacks

    return config_dict
