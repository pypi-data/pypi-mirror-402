# wintouch API Reference

This document provides a comprehensive index of all public APIs in the wintouch library.

## Overview

wintouch is a Python C extension providing direct access to the Windows Touch
Injection API for simulating touch input events on Windows 8+.

## Quick Navigation

| Category | Items |
|----------|-------|
| [Functions](#functions) | Core operations for touch injection |
| [Convenience Flags](#convenience-flags) | Pre-built flag combinations for common operations |
| [Pointer Flags](#pointer-flags) | Raw pointer state flags |
| [Touch Flags](#touch-flags) | Touch-specific flags |
| [Touch Masks](#touch-masks) | Validity masks for optional touch properties |
| [Feedback Modes](#feedback-modes) | Visual feedback configuration |

## Functions

### Initialization

| Function | Description | Documentation |
|----------|-------------|---------------|
| `initialize()` | Initialize touch injection subsystem | [initialize.md](initialize.md) |
| `is_available()` | Check if touch injection API is available | [is_available.md](is_available.md) |
| `is_initialized()` | Check if touch injection is initialized | [is_initialized.md](is_initialized.md) |
| `get_max_contacts()` | Get maximum configured simultaneous contacts | [get_max_contacts.md](get_max_contacts.md) |

### Input Injection

| Function | Description | Documentation |
|----------|-------------|---------------|
| `inject()` | Inject touch input events | [inject.md](inject.md) |

### Diagnostics

| Function | Description | Documentation |
|----------|-------------|---------------|
| `diagnose()` | Comprehensive capability diagnosis | [diagnose.md](diagnose.md) |

## Constants

### Convenience Flags

Pre-built flag combinations for common touch operations:

| Constant | Value | Description | Documentation |
|----------|-------|-------------|---------------|
| `FLAGS_DOWN` | `0x00010006` | Touch down (finger contacts screen) | [constants.md#FLAGS_DOWN](constants.md#flags_down) |
| `FLAGS_UPDATE` | `0x00020006` | Touch move (finger moves while in contact) | [constants.md#FLAGS_UPDATE](constants.md#flags_update) |
| `FLAGS_UP` | `0x00040000` | Touch up (finger leaves screen) | [constants.md#FLAGS_UP](constants.md#flags_up) |

### Pointer Flags

Raw pointer flags from the Windows API:

| Constant | Value | Description |
|----------|-------|-------------|
| `POINTER_FLAG_NONE` | `0x00000000` | No flags set |
| `POINTER_FLAG_NEW` | `0x00000001` | New pointer input |
| `POINTER_FLAG_INRANGE` | `0x00000002` | Pointer is in detection range |
| `POINTER_FLAG_INCONTACT` | `0x00000004` | Pointer is in contact with surface |
| `POINTER_FLAG_FIRSTBUTTON` | `0x00000010` | First button pressed |
| `POINTER_FLAG_PRIMARY` | `0x00002000` | Primary contact point |
| `POINTER_FLAG_CONFIDENCE` | `0x00004000` | High confidence input |
| `POINTER_FLAG_CANCELED` | `0x00008000` | Input was canceled |
| `POINTER_FLAG_DOWN` | `0x00010000` | Pointer went down |
| `POINTER_FLAG_UPDATE` | `0x00020000` | Pointer position update |
| `POINTER_FLAG_UP` | `0x00040000` | Pointer went up |

See [constants.md](constants.md) for complete documentation.

### Touch Flags

| Constant | Value | Description |
|----------|-------|-------------|
| `TOUCH_FLAG_NONE` | `0x00000000` | No touch flags |

### Touch Masks

Validity masks indicating which optional touch properties are set:

| Constant | Value | Description |
|----------|-------|-------------|
| `TOUCH_MASK_NONE` | `0x00000000` | No optional properties |
| `TOUCH_MASK_CONTACTAREA` | `0x00000001` | Contact area is valid |
| `TOUCH_MASK_ORIENTATION` | `0x00000002` | Orientation is valid |
| `TOUCH_MASK_PRESSURE` | `0x00000004` | Pressure is valid |

### Feedback Modes

Visual feedback configuration for touch injection:

| Constant | Value | Description |
|----------|-------|-------------|
| `FEEDBACK_DEFAULT` | `0x1` | Default touch visualization |
| `FEEDBACK_INDIRECT` | `0x2` | Indirect feedback mode |
| `FEEDBACK_NONE` | `0x3` | No visual feedback |

## Data Structures

### Contact Dictionary

The `inject()` function accepts a list of contact dictionaries with the following fields:

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | X coordinate in screen pixels |
| `y` | `int` | Y coordinate in screen pixels |
| `flags` | `int` | Pointer flags (use `FLAGS_DOWN`, `FLAGS_UPDATE`, `FLAGS_UP`) |

#### Optional Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `pointer_id` | `int` | List index | 0 to max_contacts-1 | Unique contact identifier |
| `pressure` | `int` | 32000 | 0-32000 | Pressure value |
| `orientation` | `int` | 90 | 0-359 | Orientation in degrees |
| `contact_width` | `int` | 4 | >0 | Contact area width in pixels |
| `contact_height` | `int` | 4 | >0 | Contact area height in pixels |

### Diagnostic Dictionary

The `diagnose()` function returns a dictionary with diagnostic information:

| Field | Type | Description |
|-------|------|-------------|
| `api_available` | `bool` | Whether touch injection API is available |
| `has_touch_digitizer` | `bool` | Whether touch hardware is detected |
| `digitizer_flags` | `int` | Raw SM_DIGITIZER value |
| `max_touch_points` | `int` | Maximum touch points supported by hardware |
| `integrated_touch` | `bool` | Has integrated touch digitizer |
| `external_touch` | `bool` | Has external touch digitizer |
| `touch_ready` | `bool` | Touch subsystem is ready |
| `init_works` | `bool` | InitializeTouchInjection succeeded |
| `init_error` | `int` | Win32 error code from initialize |
| `inject_works` | `bool` | InjectTouchInput succeeded |
| `inject_error` | `int` | Win32 error code from inject |
| `diagnosis` | `str` | Human-readable diagnosis message |

## Usage Patterns

### Basic Touch Sequence

```python
import wintouch

# Initialize
wintouch.initialize()

# Touch down
wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])

# Move (optional)
wintouch.inject([{"x": 500, "y": 400, "flags": wintouch.FLAGS_UPDATE}])

# Touch up
wintouch.inject([{"x": 500, "y": 400, "flags": wintouch.FLAGS_UP}])
```

### Multi-touch

```python
import wintouch

wintouch.initialize(max_contacts=2)

# Two fingers down
wintouch.inject([
    {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
])

# Both fingers up
wintouch.inject([
    {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
    {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
])
```

### Diagnostics

```python
import wintouch

if wintouch.is_available():
    diag = wintouch.diagnose()
    if diag['inject_works']:
        print("Touch injection is fully functional")
    else:
        print(f"Issue detected: {diag['diagnosis']}")
else:
    print("Touch injection requires Windows 8+")
```

## Error Handling

All functions may raise the following exceptions:

| Exception | Cause |
|-----------|-------|
| `ImportError` | C extension not available (non-Windows platform) |
| `ValueError` | Invalid parameter values |
| `TypeError` | Wrong parameter types |
| `KeyError` | Missing required dictionary keys |
| `RuntimeError` | Operation not allowed in current state |
| `OSError` | Windows API call failed |

## See Also

- [README.md](../../README.md) - User documentation
- [DEVELOPER.md](../DEVELOPER.md) - Developer documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [Windows Touch Injection API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-injecttouchinput) - Microsoft documentation
