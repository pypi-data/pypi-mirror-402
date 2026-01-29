"""
NSKeyedArchiver decoding utilities for macOS Terminal.app.

Terminal.app encodes colors (NSColor) and fonts (NSFont) as NSKeyedArchiver
NSData blobs in its plist configuration. This module provides utilities to
decode these without requiring PyObjC.

The NSKeyedArchiver format is a binary plist containing:
- $archiver: "NSKeyedArchiver"
- $objects: Array of archived objects
- $top: Root object reference

For NSColor, the NSRGB field contains space-separated float values as ASCII.
For NSFont, NSName and NSSize fields contain the font family and point size.
"""

import plistlib

from console_cowboy.ctec.schema import Color


def is_pyobjc_available() -> bool:
    """Check if PyObjC is available for native NSArchive operations."""
    try:
        from AppKit import NSColor  # noqa: F401
        from Foundation import NSKeyedUnarchiver  # noqa: F401

        return True
    except ImportError:
        return False


def decode_nscolor_data(data: bytes) -> Color | None:
    """
    Decode NSKeyedArchiver-encoded NSColor data to a Color object.

    Attempts PyObjC first for accuracy, falls back to manual parsing.

    Args:
        data: Raw NSData bytes containing archived NSColor

    Returns:
        Color object, or None if decoding fails
    """
    # Try PyObjC first (more accurate)
    if is_pyobjc_available():
        result = _decode_nscolor_pyobjc(data)
        if result is not None:
            return result

    # Fall back to manual parsing
    return _decode_nscolor_manual(data)


def _decode_nscolor_pyobjc(data: bytes) -> Color | None:
    """Decode NSColor using PyObjC (macOS only)."""
    try:
        from Foundation import NSData, NSKeyedUnarchiver

        nsdata = NSData.dataWithBytes_length_(data, len(data))
        nscolor = NSKeyedUnarchiver.unarchiveObjectWithData_(nsdata)

        if nscolor is None:
            return None

        # Convert to calibrated RGB color space
        rgb_color = nscolor.colorUsingColorSpaceName_("NSCalibratedRGBColorSpace")
        if rgb_color is None:
            # Try device RGB as fallback
            rgb_color = nscolor.colorUsingColorSpaceName_("NSDeviceRGBColorSpace")

        if rgb_color:
            r = int(rgb_color.redComponent() * 255)
            g = int(rgb_color.greenComponent() * 255)
            b = int(rgb_color.blueComponent() * 255)
            return Color(r=r, g=g, b=b)
    except Exception:
        pass
    return None


def _decode_nscolor_manual(data: bytes) -> Color | None:
    """
    Decode NSColor data by manually parsing the NSKeyedArchiver structure.

    NSKeyedArchiver color data typically contains an NSRGB field with
    space-separated float values encoded as ASCII bytes.
    """
    try:
        archive = plistlib.loads(data)

        if archive.get("$archiver") != "NSKeyedArchiver":
            return None

        objects = archive.get("$objects", [])

        # Look for NSRGB data in objects (calibrated RGB)
        for obj in objects:
            if isinstance(obj, dict):
                # Check for NSRGB (calibrated RGB as ASCII floats)
                if "NSRGB" in obj:
                    rgb_data = obj["NSRGB"]
                    if isinstance(rgb_data, bytes):
                        rgb_str = rgb_data.decode("ascii").strip()
                        parts = rgb_str.split()
                        if len(parts) >= 3:
                            r = int(float(parts[0]) * 255)
                            g = int(float(parts[1]) * 255)
                            b = int(float(parts[2]) * 255)
                            return Color(r=r, g=g, b=b)

                # Check for NSRGB as string (some formats)
                if "NSRGB" in obj and isinstance(obj["NSRGB"], str):
                    parts = obj["NSRGB"].split()
                    if len(parts) >= 3:
                        r = int(float(parts[0]) * 255)
                        g = int(float(parts[1]) * 255)
                        b = int(float(parts[2]) * 255)
                        return Color(r=r, g=g, b=b)

                # Check for individual color components (device RGB)
                if "NSColorSpace" in obj:
                    # Named color space with components
                    if "NSComponents" in obj:
                        components = obj["NSComponents"]
                        if isinstance(components, bytes):
                            # Components stored as binary data
                            comp_str = components.decode("ascii").strip()
                            parts = comp_str.split()
                            if len(parts) >= 3:
                                r = int(float(parts[0]) * 255)
                                g = int(float(parts[1]) * 255)
                                b = int(float(parts[2]) * 255)
                                return Color(r=r, g=g, b=b)
    except Exception:
        pass
    return None


def decode_nsfont_data(data: bytes) -> tuple[str, float] | None:
    """
    Decode NSKeyedArchiver-encoded NSFont data.

    Args:
        data: Raw NSData bytes containing archived NSFont

    Returns:
        Tuple of (font_family, font_size), or None if decoding fails
    """
    # Try PyObjC first
    if is_pyobjc_available():
        result = _decode_nsfont_pyobjc(data)
        if result is not None:
            return result

    # Fall back to manual parsing
    return _decode_nsfont_manual(data)


def _decode_nsfont_pyobjc(data: bytes) -> tuple[str, float] | None:
    """Decode NSFont using PyObjC (macOS only)."""
    try:
        from Foundation import NSData, NSKeyedUnarchiver

        nsdata = NSData.dataWithBytes_length_(data, len(data))
        nsfont = NSKeyedUnarchiver.unarchiveObjectWithData_(nsdata)

        if nsfont is None:
            return None

        family = nsfont.familyName()
        size = nsfont.pointSize()
        return (family, float(size))
    except Exception:
        pass
    return None


def _decode_nsfont_manual(data: bytes) -> tuple[str, float] | None:
    """
    Decode NSFont data by manually parsing the NSKeyedArchiver structure.

    NSFont archives contain NSName (font name) and NSSize (point size).
    """
    try:
        archive = plistlib.loads(data)

        if archive.get("$archiver") != "NSKeyedArchiver":
            return None

        objects = archive.get("$objects", [])

        font_name = None
        font_size = None

        # Look for font attributes in objects
        for obj in objects:
            if isinstance(obj, dict):
                # NSName contains the font name
                if "NSName" in obj:
                    name_ref = obj["NSName"]
                    # Could be a reference (UID) or direct string
                    if isinstance(name_ref, str):
                        font_name = name_ref
                    elif hasattr(name_ref, "data"):
                        # plistlib.UID object - look up in objects array
                        idx = (
                            name_ref.data
                            if hasattr(name_ref, "data")
                            else int(name_ref)
                        )
                        if 0 <= idx < len(objects) and isinstance(objects[idx], str):
                            font_name = objects[idx]

                # NSSize contains the point size
                if "NSSize" in obj:
                    try:
                        font_size = float(obj["NSSize"])
                    except (TypeError, ValueError):
                        pass

        # Also check for font descriptor style storage
        for obj in objects:
            if isinstance(obj, dict):
                # Some fonts store name directly
                if "NSFontNameAttribute" in obj:
                    name_ref = obj["NSFontNameAttribute"]
                    if isinstance(name_ref, str):
                        font_name = name_ref
                    elif hasattr(name_ref, "data"):
                        idx = (
                            name_ref.data
                            if hasattr(name_ref, "data")
                            else int(name_ref)
                        )
                        if 0 <= idx < len(objects) and isinstance(objects[idx], str):
                            font_name = objects[idx]

                if "NSFontSizeAttribute" in obj:
                    try:
                        font_size = float(obj["NSFontSizeAttribute"])
                    except (TypeError, ValueError):
                        pass

        if font_name and font_size:
            return (font_name, font_size)
    except Exception:
        pass
    return None


def encode_nscolor_data(color: Color) -> bytes | None:
    """
    Encode a Color to NSKeyedArchiver NSColor data.

    Uses PyObjC if available for proper NSColor encoding.
    Falls back to creating a minimal NSKeyedArchiver structure.

    Args:
        color: Color object to encode

    Returns:
        NSData bytes, or None if encoding fails
    """
    if is_pyobjc_available():
        return _encode_nscolor_pyobjc(color)
    return _encode_nscolor_manual(color)


def _encode_nscolor_pyobjc(color: Color) -> bytes | None:
    """Encode NSColor using PyObjC (macOS only)."""
    try:
        from AppKit import NSColor
        from Foundation import NSKeyedArchiver

        nscolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
            color.r / 255.0, color.g / 255.0, color.b / 255.0, 1.0
        )
        data = NSKeyedArchiver.archivedDataWithRootObject_(nscolor)
        return bytes(data)
    except Exception:
        pass
    return None


def _encode_nscolor_manual(color: Color) -> bytes | None:
    """
    Encode a Color as NSKeyedArchiver NSColor data without PyObjC.

    Creates a minimal NSKeyedArchiver structure with NSRGB data.
    """
    try:
        # Create RGB string (space-separated floats)
        rgb_str = f"{color.r / 255.0} {color.g / 255.0} {color.b / 255.0}"

        # Build NSKeyedArchiver structure for NSColor
        archive = {
            "$archiver": "NSKeyedArchiver",
            "$version": 100000,
            "$top": {"root": plistlib.UID(1)},
            "$objects": [
                "$null",
                {
                    "$class": plistlib.UID(2),
                    "NSColorSpace": 1,  # Calibrated RGB
                    "NSRGB": rgb_str.encode("ascii"),
                },
                {
                    "$classname": "NSColor",
                    "$classes": ["NSColor", "NSObject"],
                },
            ],
        }

        return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)
    except Exception:
        pass
    return None


def encode_nsfont_data(family: str, size: float) -> bytes | None:
    """
    Encode font information to NSKeyedArchiver NSFont data.

    Uses PyObjC if available for proper NSFont encoding.

    Args:
        family: Font family name
        size: Font size in points

    Returns:
        NSData bytes, or None if encoding fails
    """
    if is_pyobjc_available():
        return _encode_nsfont_pyobjc(family, size)
    return _encode_nsfont_manual(family, size)


def _encode_nsfont_pyobjc(family: str, size: float) -> bytes | None:
    """Encode NSFont using PyObjC (macOS only)."""
    try:
        from AppKit import NSFont, NSFontManager
        from Foundation import NSKeyedArchiver

        # Try to find the font by family name
        font_manager = NSFontManager.sharedFontManager()
        font = font_manager.fontWithFamily_traits_weight_size_(family, 0, 5, size)

        if font is None:
            # Try as PostScript name
            font = NSFont.fontWithName_size_(family, size)

        if font is None:
            # Fall back to user fixed pitch font
            font = NSFont.userFixedPitchFontOfSize_(size)

        if font:
            data = NSKeyedArchiver.archivedDataWithRootObject_(font)
            return bytes(data)
    except Exception:
        pass
    return None


def _encode_nsfont_manual(family: str, size: float) -> bytes | None:
    """
    Encode font as NSKeyedArchiver NSFont data without PyObjC.

    Creates a minimal NSKeyedArchiver structure with font attributes.
    Note: This may not be fully compatible with all Terminal.app versions.
    """
    try:
        # Build NSKeyedArchiver structure for NSFont
        archive = {
            "$archiver": "NSKeyedArchiver",
            "$version": 100000,
            "$top": {"root": plistlib.UID(1)},
            "$objects": [
                "$null",
                {
                    "$class": plistlib.UID(3),
                    "NSName": plistlib.UID(2),
                    "NSSize": size,
                    "NSfFlags": 16,  # Fixed pitch flag
                },
                family,
                {
                    "$classname": "NSFont",
                    "$classes": ["NSFont", "NSObject"],
                },
            ],
        }

        return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)
    except Exception:
        pass
    return None
