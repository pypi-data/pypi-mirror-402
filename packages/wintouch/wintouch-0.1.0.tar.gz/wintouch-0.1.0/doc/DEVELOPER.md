# Developer Documentation

This document provides comprehensive technical documentation for developers working
on or extending the wintouch library.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [C Extension Details](#c-extension-details)
- [Python Wrapper](#python-wrapper)
- [Build System](#build-system)
- [Memory Management](#memory-management)
- [Error Handling](#error-handling)
- [Thread Safety](#thread-safety)
- [Testing](#testing)
- [Debugging](#debugging)
- [Performance Considerations](#performance-considerations)
- [Extending the Library](#extending-the-library)

## Architecture Overview

wintouch is structured as a two-layer system:

```
┌─────────────────────────────────────────────────────────────┐
│                     User Application                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Python Wrapper (wintouch/__init__.py)        │
│  • High-level API                                           │
│  • Convenience flag combinations                            │
│  • Cross-platform import safety                             │
│  • Constants export                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              C Extension (src/_wintouch/module.c)           │
│  • Direct Win32 API access                                  │
│  • Dynamic function loading                                 │
│  • Python <-> C data conversion                             │
│  • Module state management                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Windows user32.dll                     │
│  • InitializeTouchInjection()                               │
│  • InjectTouchInput()                                       │
└─────────────────────────────────────────────────────────────┘
```

### Design Decisions

1. **Dynamic Loading**: Touch injection functions are loaded at runtime via
   `GetProcAddress()` rather than compile-time linking. This allows the module
   to gracefully fail on pre-Windows 8 systems instead of crashing on import.

2. **Thin Wrapper**: The C extension is deliberately minimal, providing only
   the necessary translation between Python and Win32 APIs. Higher-level
   abstractions (gesture helpers, etc.) belong in Python.

3. **Stub Fallback**: On non-Windows platforms, stub functions raise
   `ImportError` with helpful messages, allowing package import for
   documentation and type checking.

## Project Structure

```
wintouch/
├── src/
│   └── _wintouch/
│       └── module.c        # C extension implementation
├── wintouch/
│   ├── __init__.py         # Python wrapper and public API
│   └── py.typed            # PEP 561 marker for type checkers
├── doc/
│   ├── DEVELOPER.md        # This file
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   └── api/
│       ├── INDEX.md        # API documentation index
│       ├── initialize.md   # initialize() documentation
│       ├── inject.md       # inject() documentation
│       └── ...             # Other API documentation
├── tests/
│   └── ...                 # Test suite
├── pyproject.toml          # Package metadata (PEP 621)
├── setup.py                # C extension build configuration
└── README.md               # User documentation
```

## C Extension Details

### Module State

The C extension maintains global state for the touch injection subsystem:

```c
static HMODULE hUser32 = NULL;                           // Loaded user32.dll handle
static PFN_InitializeTouchInjection pfnInitializeTouchInjection = NULL;  // Function pointer
static PFN_InjectTouchInput pfnInjectTouchInput = NULL;  // Function pointer
static int touch_initialized = 0;                        // Initialization flag
static UINT32 max_contacts = 0;                          // Configured max contacts
```

**Important**: This state is per-process. Multiple Python interpreters in the
same process share this state.

### Dynamic Function Loading

The `load_touch_functions()` helper loads touch injection functions at runtime:

```c
static int load_touch_functions(void) {
    if (hUser32 != NULL) {
        return 1;  // Already loaded
    }

    hUser32 = LoadLibraryA("user32.dll");
    if (hUser32 == NULL) {
        return 0;
    }

    pfnInitializeTouchInjection = (PFN_InitializeTouchInjection)
        GetProcAddress(hUser32, "InitializeTouchInjection");
    pfnInjectTouchInput = (PFN_InjectTouchInput)
        GetProcAddress(hUser32, "InjectTouchInput");

    if (pfnInitializeTouchInjection == NULL || pfnInjectTouchInput == NULL) {
        FreeLibrary(hUser32);
        hUser32 = NULL;
        return 0;
    }

    return 1;
}
```

This pattern:
- Returns `1` (success) if already loaded (idempotent)
- Loads user32.dll and resolves function addresses
- Returns `0` (failure) and cleans up if functions not found
- Makes `is_available()` a cheap operation after first call

### Touch Support Detection and Graceful Failure

The C extension uses a three-layer detection system to determine touch support
and provide meaningful error messages at each failure point.

#### Layer 1: API Existence Check

```
LoadLibraryA("user32.dll")
    │
    ├─ NULL? → System broken (extremely rare)
    │
    ▼
GetProcAddress("InitializeTouchInjection")
GetProcAddress("InjectTouchInput")
    │
    ├─ Either NULL? → Windows < 8 (functions don't exist in older Windows)
    │
    ▼
API available (is_available() returns True)
```

This check is performed by `load_touch_functions()` and cached. The functions
`InitializeTouchInjection` and `InjectTouchInput` were added in Windows 8;
older Windows versions don't export them from user32.dll.

#### Layer 2: Hardware Detection (diagnose only)

The `diagnose()` function queries system metrics to detect touch hardware:

```c
int digitizer = GetSystemMetrics(SM_DIGITIZER);    // 94
int max_touches = GetSystemMetrics(SM_MAXIMUMTOUCHES);  // 95
```

The `SM_DIGITIZER` value is a bitmask:

| Flag | Value | Meaning |
|------|-------|---------|
| `NID_INTEGRATED_TOUCH` | `0x01` | Has integrated touchscreen |
| `NID_EXTERNAL_TOUCH` | `0x02` | Has external touch device |
| `NID_MULTI_INPUT` | `0x40` | Supports multiple simultaneous contacts |
| `NID_READY` | `0x80` | Touch input subsystem is ready |

**Key insight**: `has_touch_digitizer` is true when either `NID_INTEGRATED_TOUCH`
or `NID_EXTERNAL_TOUCH` is set. If neither is set, touch injection will fail
with ERROR_INVALID_PARAMETER (87).

#### Layer 3: Functional Test (diagnose only)

The `diagnose()` function actually attempts the operations:

```
InitializeTouchInjection(1, FEEDBACK_DEFAULT)
    │
    ├─ Fail + Error 5?  → ACCESS_DENIED (need admin or another process owns it)
    ├─ Fail + Error 87? → INVALID_PARAMETER (rare at init stage)
    │
    ▼
InjectTouchInput(test_contact)
    │
    ├─ Fail + Error 5?  → ACCESS_DENIED
    ├─ Fail + Error 87? → INVALID_PARAMETER (usually means no touch hardware)
    │
    ▼
Success → Touch injection fully functional
```

#### Graceful Failure Matrix

| Stage | Failure Condition | Detection | User-Facing Error |
|-------|-------------------|-----------|-------------------|
| Import | Non-Windows platform | Python ImportError | Stub raises ImportError with message |
| `is_available()` | Windows < 8 | `GetProcAddress` returns NULL | Returns `False` |
| `initialize()` | Windows < 8 | `load_touch_functions()` fails | `OSError: Touch injection API not available (requires Windows 8+)` |
| `initialize()` | Permission denied | `InitializeTouchInjection` returns FALSE, error 5 | `OSError: InitializeTouchInjection failed (error 5)` |
| `initialize()` | Another process owns | Same as permission denied | Same error message |
| `inject()` | Not initialized | `touch_initialized == 0` | `RuntimeError: Touch injection not initialized. Call initialize() first.` |
| `inject()` | No touch hardware | `InjectTouchInput` returns FALSE, error 87 | `OSError: InjectTouchInput failed (error 87)` |
| `inject()` | Bad coordinates | `InjectTouchInput` returns FALSE, error 87 | Same error message |

#### Diagnostic Correlation

The `diagnose()` function correlates hardware detection with functional test results
to provide meaningful diagnosis messages:

```c
if (inject_error == 87) {
    if (!has_touch) {
        // "No touch digitizer detected... Touch injection requires touch hardware."
    } else if (!ready) {
        // "Touch hardware detected but not ready..."
    } else {
        // "Touch hardware present and ready, but injection failed..."
    }
}
```

This allows users to understand WHY touch injection failed, not just that it failed.

### POINTER_TOUCH_INFO Structure

The core data structure for touch injection is `POINTER_TOUCH_INFO`:

```c
typedef struct tagPOINTER_TOUCH_INFO {
    POINTER_INFO pointerInfo;    // Base pointer information
    TOUCH_FLAGS touchFlags;      // Touch-specific flags
    TOUCH_MASK touchMask;        // Validity mask for optional fields
    RECT rcContact;              // Contact area rectangle
    RECT rcContactRaw;           // Raw contact area (unused)
    UINT32 orientation;          // Orientation in degrees (0-359)
    UINT32 pressure;             // Pressure (0-32000)
} POINTER_TOUCH_INFO;

typedef struct tagPOINTER_INFO {
    POINTER_INPUT_TYPE pointerType;   // PT_TOUCH for touch input
    UINT32 pointerId;                 // Unique contact identifier
    UINT32 frameId;                   // Frame ID (auto-generated)
    POINTER_FLAGS pointerFlags;       // State flags
    HANDLE sourceDevice;              // Source device (unused)
    HWND hwndTarget;                  // Target window (unused)
    POINT ptPixelLocation;            // Screen coordinates
    POINT ptHimetricLocation;         // High-metric coordinates (unused)
    POINT ptPixelLocationRaw;         // Raw coordinates (unused)
    POINT ptHimetricLocationRaw;      // Raw high-metric (unused)
    DWORD dwTime;                     // Event time (auto-generated)
    UINT32 historyCount;              // History count (unused)
    INT32 InputData;                  // Input data (unused)
    DWORD dwKeyStates;                // Key states (unused)
    UINT64 PerformanceCount;          // Performance counter (unused)
    POINTER_BUTTON_CHANGE_TYPE ButtonChangeType;  // Button change (unused)
} POINTER_INFO;
```

### Contact Dictionary Conversion

The `inject()` function converts Python dictionaries to `POINTER_TOUCH_INFO`:

```c
// Required fields
contacts_arr[i].pointerInfo.pointerType = PT_TOUCH;
contacts_arr[i].pointerInfo.pointerId = (UINT32)i;       // Default to index
contacts_arr[i].pointerInfo.ptPixelLocation.x = x;
contacts_arr[i].pointerInfo.ptPixelLocation.y = y;
contacts_arr[i].pointerInfo.pointerFlags = flags;

// Microsoft sample defaults
contacts_arr[i].touchFlags = TOUCH_FLAG_NONE;
contacts_arr[i].touchMask = TOUCH_MASK_CONTACTAREA |
                            TOUCH_MASK_ORIENTATION |
                            TOUCH_MASK_PRESSURE;
contacts_arr[i].orientation = 90;    // Perpendicular to screen
contacts_arr[i].pressure = 32000;    // Default pressure

// Contact area (centered on touch point)
contacts_arr[i].rcContact.left = x - contact_width / 2;
contacts_arr[i].rcContact.right = x + contact_width / 2;
contacts_arr[i].rcContact.top = y - contact_height / 2;
contacts_arr[i].rcContact.bottom = y + contact_height / 2;
```

**Critical**: The array must be zero-initialized with `calloc()`. The Windows
API may check unused fields for specific values.

### Critical Implementation Lessons

These lessons were learned through extensive trial and error. Following Microsoft's
official sample code exactly is essential - many "reasonable" variations fail.

#### Minimal Flags Are Required

Only specific flag combinations work. Adding extra flags causes `ERROR_INVALID_PARAMETER`:

```c
// DON'T DO THIS - causes ERROR_INVALID_PARAMETER (87)
FLAGS_DOWN = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT |
             POINTER_FLAG_PRIMARY | POINTER_FLAG_CONFIDENCE;  // Extra flags!

// DO THIS - works correctly
FLAGS_DOWN = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT;
FLAGS_UP = POINTER_FLAG_UP;  // Just UP, no other flags
```

Adding `POINTER_FLAG_PRIMARY` or `POINTER_FLAG_CONFIDENCE` causes error 87, even
though these seem like reasonable additions.

#### Fields That Must Be Zero/NULL

The following fields should NOT be set - leave them zeroed:
- `frameId` - system auto-generates
- `dwTime` - system auto-generates
- `sourceDevice` - NULL for injected touch
- `hwndTarget` - NULL for screen coordinates
- `ptPixelLocationRaw` - not required
- `ptHimetricLocation` - not required
- `PerformanceCount` - not required

Setting these fields (even to seemingly valid values) can cause injection failures.

#### Error 87 Is Not a Permission Issue

`ERROR_INVALID_PARAMETER` (87) indicates bad touch data structure, not permissions.
If you get error 87 with Administrator rights, check:
1. Coordinates are within screen bounds
2. Using minimal flag combinations
3. Structure is zero-initialized
4. Not setting fields that should be NULL

#### Touch Hardware Required

**Touch injection requires touch hardware.** The Windows Touch Injection API does
not work on systems without a touch digitizer. This is a Windows limitation, not
a limitation of this library.

Systems must have:
- Touch digitizer hardware present
- Touch capability reported via `GetSystemMetrics(SM_DIGITIZER)`

Use `diagnose()` to check `has_touch_digitizer` before attempting injection.

#### What Doesn't Affect Touch Injection

The following do NOT prevent touch injection:
- Hyper-V enabled
- VBS/HVCI (Virtualization Based Security) enabled

### Constants Definition

The C extension defines Win32 constants that may not be present in older SDK headers:

```c
#ifndef POINTER_FLAG_NONE
#define POINTER_FLAG_NONE           0x00000000
#define POINTER_FLAG_NEW            0x00000001
#define POINTER_FLAG_INRANGE        0x00000002
// ... etc
#endif
```

This ensures compilation succeeds regardless of SDK version.

## Python Wrapper

### Import Safety

The Python wrapper handles import failures gracefully:

```python
try:
    from _wintouch import (
        initialize, inject, is_available, is_initialized,
        get_max_contacts, diagnose, ...constants...
    )
    _AVAILABLE = True
except ImportError as e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(e)

    def _not_available(*args, **kwargs):
        raise ImportError(
            f"wintouch C extension not available: {_IMPORT_ERROR}. "
            "This package requires Windows 8+ and must be built from source."
        )

    initialize = _not_available
    inject = _not_available
    # ... stub assignments
```

This allows:
- Package import on non-Windows systems
- Documentation generation
- Type checking with mypy
- Clear error messages when used

### Convenience Flags

The wrapper defines high-level flag combinations based on Microsoft's sample code:

```python
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
```

These match the exact combinations used in Microsoft's official Touch Injection API sample.

## Build System

### setup.py

The C extension build is configured in `setup.py`:

```python
from setuptools import setup, Extension

ext_modules = []
if sys.platform == "win32":
    ext_modules.append(
        Extension(
            "_wintouch",
            sources=["src/_wintouch/module.c"],
            libraries=["user32"],
        )
    )

setup(ext_modules=ext_modules)
```

### pyproject.toml

Package metadata follows PEP 621:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "wintouch"
version = "0.1.0"
requires-python = ">=3.8"
```

### Build Commands

```bash
# Build extension in-place (for development)
python setup.py build_ext --inplace

# Build wheel
python -m build

# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Memory Management

### Allocation

The C extension allocates memory for the contact array:

```c
contacts_arr = (POINTER_TOUCH_INFO *)calloc(count, sizeof(POINTER_TOUCH_INFO));
if (contacts_arr == NULL) {
    PyErr_NoMemory();
    return NULL;
}
```

**Important**: `calloc()` is used instead of `malloc()` to zero-initialize the
array. The Windows API may check unused fields.

### Deallocation

Memory is freed in all code paths using a cleanup label:

```c
cleanup:
    free(contacts_arr);
    return result;
```

This ensures proper cleanup on both success and error paths.

### Reference Counting

Python object reference counting follows standard patterns:

```c
// Borrowing a reference (no INCREF needed)
PyObject *contact_dict = PyList_GetItem(contacts_list, i);

// Creating a new reference (INCREF needed)
result = Py_True;
Py_INCREF(result);

// Dictionary functions return borrowed references
val = PyDict_GetItemString(contact_dict, "x");  // Borrowed, no DECREF
```

## Error Handling

### C Extension Errors

Errors in the C extension set Python exceptions:

```c
// Value errors
if (max_contacts_arg < 1 || max_contacts_arg > 10) {
    PyErr_SetString(PyExc_ValueError, "max_contacts must be between 1 and 10");
    return NULL;
}

// Key errors
if (val == NULL) {
    PyErr_SetString(PyExc_KeyError, "Contact missing required 'x' key");
    goto cleanup;
}

// OS errors with Win32 error code
if (!pfnInitializeTouchInjection(max_contacts_arg, feedback_mode)) {
    DWORD err = GetLastError();
    PyErr_Format(PyExc_OSError,
        "InitializeTouchInjection failed (error %lu)", err);
    return NULL;
}

// Runtime errors
if (!touch_initialized) {
    PyErr_SetString(PyExc_RuntimeError,
        "Touch injection not initialized. Call initialize() first.");
    return NULL;
}
```

### Error Propagation

After calling Python C API functions, always check for errors:

```c
x = (LONG)PyLong_AsLong(val);
// ... more conversions ...

if (PyErr_Occurred()) {
    goto cleanup;
}
```

### Win32 Error Codes

Common error codes and their meanings:

| Code | Name | Cause |
|------|------|-------|
| 5 | ERROR_ACCESS_DENIED | Permission denied |
| 87 | ERROR_INVALID_PARAMETER | Invalid parameter or no touch hardware |
| 1168 | ERROR_NOT_FOUND | Operation not initialized |

## Thread Safety

### Global State

The module's global state is **not thread-safe**. Concurrent calls from multiple
threads may cause undefined behavior.

**Recommendation**: Synchronize access at the application level if using threads.

### GIL Considerations

All C extension functions hold the GIL throughout execution. This is appropriate
because:
- Touch injection is typically UI-driven (single-threaded)
- Win32 API calls are fast
- No I/O blocking occurs

For applications needing concurrent injection, consider:
- Using a dedicated touch injection thread with a queue
- Releasing the GIL around `InjectTouchInput()` calls (requires careful state management)

## Testing

### Test Environment Requirements

- Windows 8 or later
- May require Administrator privileges
- Some tests may require touch hardware

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_basic.py::test_is_available
```

### Writing Tests

```python
import pytest
import wintouch

def test_is_available():
    """Test that is_available returns a boolean."""
    result = wintouch.is_available()
    assert isinstance(result, bool)

def test_initialize_valid_range():
    """Test initialize with valid max_contacts values."""
    if not wintouch.is_available():
        pytest.skip("Touch injection not available")

    wintouch.initialize(max_contacts=1)
    assert wintouch.is_initialized()
    assert wintouch.get_max_contacts() == 1

def test_initialize_invalid_max_contacts():
    """Test initialize rejects invalid max_contacts."""
    if not wintouch.is_available():
        pytest.skip("Touch injection not available")

    with pytest.raises(ValueError):
        wintouch.initialize(max_contacts=0)

    with pytest.raises(ValueError):
        wintouch.initialize(max_contacts=11)
```

### Mocking for Non-Windows Testing

For cross-platform CI, mock the C extension:

```python
import sys
from unittest.mock import MagicMock

# Mock the C extension before importing wintouch
sys.modules['_wintouch'] = MagicMock()

import wintouch

def test_wrapper_exposes_flags():
    """Test that convenience flags are defined."""
    assert hasattr(wintouch, 'FLAGS_DOWN')
    assert hasattr(wintouch, 'FLAGS_UPDATE')
    assert hasattr(wintouch, 'FLAGS_UP')
```

## Debugging

### Debug Build

Build with debug symbols:

```bash
# With MSVC
set DISTUTILS_DEBUG=1
python setup.py build_ext --inplace --debug

# Debug in Visual Studio
devenv /debugexe python.exe script.py
```

### Common Issues

#### Crash on InjectTouchInput

Usually caused by uninitialized `POINTER_TOUCH_INFO` fields. Ensure:
- Array is allocated with `calloc()`, not `malloc()`
- All required fields are set
- `pointerType` is `PT_TOUCH`

#### ERROR_INVALID_PARAMETER

Check:
- Touch hardware presence (use `diagnose()`)
- Coordinate values are within screen bounds
- `touchMask` matches which optional fields are set

#### Reference Count Errors

Debug with:
```bash
python -X dev script.py  # Development mode
```

Or build Python with `--with-pydebug` and use `Py_REFCNT()`.

### Diagnostic Function

The `diagnose()` function provides comprehensive debugging:

```python
import wintouch

if wintouch.is_available():
    diag = wintouch.diagnose()
    print("API Available:", diag['api_available'])
    print("Touch Digitizer:", diag['has_touch_digitizer'])
    print("Digitizer Flags:", hex(diag['digitizer_flags']))
    print("Max Touch Points:", diag['max_touch_points'])
    print("Init Works:", diag['init_works'])
    print("Init Error:", diag['init_error'])
    print("Inject Works:", diag['inject_works'])
    print("Inject Error:", diag['inject_error'])
    print("Diagnosis:", diag['diagnosis'])
```

## Performance Considerations

### Injection Latency

Touch injection adds minimal latency:
- Function call overhead: ~1-5 microseconds
- Win32 API call: ~10-100 microseconds
- Total per injection: typically <1ms

### Batch Injection

For multi-touch, inject all contacts in a single call:

```python
# Efficient: single API call
wintouch.inject([
    {"x": 100, "y": 200, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 300, "y": 200, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
])

# Less efficient: two API calls
wintouch.inject([{"x": 100, "y": 200, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN}])
wintouch.inject([{"x": 300, "y": 200, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN}])
```

### Memory Allocation

Each `inject()` call allocates and frees a contact array. For extremely
high-frequency injection (>1000/sec), consider pooling at the Python level.

## Extending the Library

### Adding New Functions

1. **Implement in C** (`module.c`):

```c
static PyObject* wintouch_new_function(PyObject *self, PyObject *args) {
    // Implementation
    Py_RETURN_NONE;
}
```

2. **Add to method table**:

```c
static PyMethodDef wintouch_methods[] = {
    // ... existing methods ...
    {"new_function", wintouch_new_function, METH_VARARGS,
     "Description of new function"},
    {NULL, NULL, 0, NULL}
};
```

3. **Export in Python wrapper**:

```python
from _wintouch import (
    # ... existing imports ...
    new_function,
)

__all__ = [
    # ... existing exports ...
    "new_function",
]
```

4. **Write documentation** in `doc/api/new_function.md`

5. **Write tests** in `tests/test_new_function.py`

### Adding New Constants

1. **Define in C** (if needed for SDK compatibility):

```c
#ifndef NEW_CONSTANT
#define NEW_CONSTANT 0x00000001
#endif
```

2. **Export from module**:

```c
PyModule_AddIntConstant(m, "NEW_CONSTANT", NEW_CONSTANT);
```

3. **Add fallback in Python** (for non-Windows):

```python
except ImportError:
    # ... existing stubs ...
    NEW_CONSTANT = 0x00000001
```

4. **Document** in `doc/api/constants.md`

### Adding Gesture Helpers

High-level gesture functions should be implemented in Python, not C:

```python
# wintouch/gestures.py (new file)

import wintouch
import time

def swipe(start_x, start_y, end_x, end_y, duration=0.3, steps=20):
    """Perform a swipe gesture."""
    if not wintouch.is_initialized():
        wintouch.initialize()

    wintouch.inject([{"x": start_x, "y": start_y, "flags": wintouch.FLAGS_DOWN}])

    for i in range(1, steps + 1):
        t = i / steps
        x = int(start_x + (end_x - start_x) * t)
        y = int(start_y + (end_y - start_y) * t)
        wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_UPDATE}])
        time.sleep(duration / steps)

    wintouch.inject([{"x": end_x, "y": end_y, "flags": wintouch.FLAGS_UP}])
```

## See Also

- [README.md](../README.md) - User documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [doc/api/INDEX.md](api/INDEX.md) - API reference
- [Microsoft Touch Injection API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-injecttouchinput)
