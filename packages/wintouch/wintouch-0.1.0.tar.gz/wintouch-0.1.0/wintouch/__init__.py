"""
wintouch - Windows Touch Injection API for Python

A Python C extension providing direct access to the Windows Touch Injection API
(InitializeTouchInjection, InjectTouchInput) for simulating touch events.

Requires Windows 8 or later and Administrator privileges for touch injection.

Example:
    >>> import wintouch
    >>> wintouch.initialize(max_contacts=2)
    >>> wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
    >>> wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_UP}])
"""

__version__ = "0.1.0"

# Try to import from C extension
try:
    from _wintouch import (
        initialize,
        inject,
        is_available,
        is_initialized,
        get_max_contacts,
        diagnose,
        # Pointer flags
        POINTER_FLAG_NONE,
        POINTER_FLAG_NEW,
        POINTER_FLAG_INRANGE,
        POINTER_FLAG_INCONTACT,
        POINTER_FLAG_FIRSTBUTTON,
        POINTER_FLAG_PRIMARY,
        POINTER_FLAG_CONFIDENCE,
        POINTER_FLAG_CANCELED,
        POINTER_FLAG_DOWN,
        POINTER_FLAG_UPDATE,
        POINTER_FLAG_UP,
        # Touch flags
        TOUCH_FLAG_NONE,
        # Touch masks
        TOUCH_MASK_NONE,
        TOUCH_MASK_CONTACTAREA,
        TOUCH_MASK_ORIENTATION,
        TOUCH_MASK_PRESSURE,
        # Feedback modes
        FEEDBACK_DEFAULT,
        FEEDBACK_INDIRECT,
        FEEDBACK_NONE,
    )
    _AVAILABLE = True
except ImportError as e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(e)

    # Provide stub functions that raise helpful errors
    def _not_available(*args, **kwargs):
        raise ImportError(
            f"wintouch C extension not available: {_IMPORT_ERROR}. "
            "This package requires Windows 8+ and must be built from source."
        )

    initialize = _not_available
    inject = _not_available
    diagnose = _not_available
    is_available = lambda: False
    is_initialized = lambda: False
    get_max_contacts = lambda: 0

    # Define constants for documentation/type checking
    POINTER_FLAG_NONE = 0x00000000
    POINTER_FLAG_NEW = 0x00000001
    POINTER_FLAG_INRANGE = 0x00000002
    POINTER_FLAG_INCONTACT = 0x00000004
    POINTER_FLAG_FIRSTBUTTON = 0x00000010
    POINTER_FLAG_PRIMARY = 0x00002000
    POINTER_FLAG_CONFIDENCE = 0x00004000
    POINTER_FLAG_CANCELED = 0x00008000
    POINTER_FLAG_DOWN = 0x00010000
    POINTER_FLAG_UPDATE = 0x00020000
    POINTER_FLAG_UP = 0x00040000
    TOUCH_FLAG_NONE = 0x00000000
    TOUCH_MASK_NONE = 0x00000000
    TOUCH_MASK_CONTACTAREA = 0x00000001
    TOUCH_MASK_ORIENTATION = 0x00000002
    TOUCH_MASK_PRESSURE = 0x00000004
    FEEDBACK_DEFAULT = 0x1
    FEEDBACK_INDIRECT = 0x2
    FEEDBACK_NONE = 0x3

# Convenience flag combinations for common operations
# Based on Microsoft's official sample code:
# https://learn.microsoft.com/en-us/archive/technet-wiki/6460.windows-8-simulating-touch-input-using-touch-injection-api

FLAGS_DOWN = (
    POINTER_FLAG_DOWN |
    POINTER_FLAG_INRANGE |
    POINTER_FLAG_INCONTACT
)

FLAGS_UPDATE = (
    POINTER_FLAG_UPDATE |
    POINTER_FLAG_INRANGE |
    POINTER_FLAG_INCONTACT
)

FLAGS_UP = POINTER_FLAG_UP

__all__ = [
    # Functions
    "initialize",
    "inject",
    "is_available",
    "is_initialized",
    "get_max_contacts",
    "diagnose",
    # Convenience flag combos
    "FLAGS_DOWN",
    "FLAGS_UPDATE",
    "FLAGS_UP",
    # Raw pointer flags
    "POINTER_FLAG_NONE",
    "POINTER_FLAG_NEW",
    "POINTER_FLAG_INRANGE",
    "POINTER_FLAG_INCONTACT",
    "POINTER_FLAG_FIRSTBUTTON",
    "POINTER_FLAG_PRIMARY",
    "POINTER_FLAG_CONFIDENCE",
    "POINTER_FLAG_CANCELED",
    "POINTER_FLAG_DOWN",
    "POINTER_FLAG_UPDATE",
    "POINTER_FLAG_UP",
    # Touch flags
    "TOUCH_FLAG_NONE",
    # Touch masks
    "TOUCH_MASK_NONE",
    "TOUCH_MASK_CONTACTAREA",
    "TOUCH_MASK_ORIENTATION",
    "TOUCH_MASK_PRESSURE",
    # Feedback modes
    "FEEDBACK_DEFAULT",
    "FEEDBACK_INDIRECT",
    "FEEDBACK_NONE",
]
