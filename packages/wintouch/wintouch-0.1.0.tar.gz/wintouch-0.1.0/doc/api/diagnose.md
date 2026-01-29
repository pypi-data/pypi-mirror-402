# diagnose(3) - wintouch

## NAME

diagnose - perform comprehensive touch injection capability diagnosis

## SYNOPSIS

```python
import wintouch

result = wintouch.diagnose()
```

## DESCRIPTION

The `diagnose()` function performs a comprehensive diagnostic test of the
touch injection subsystem, returning detailed information about the system's
capabilities and any issues detected.

### Detection Process

The function performs a three-layer detection:

**Layer 1: API Existence**
- Attempts to load `InitializeTouchInjection` and `InjectTouchInput` from user32.dll
- If either function is missing, the API is unavailable (Windows < 8)

**Layer 2: Hardware Detection**
- Calls `GetSystemMetrics(SM_DIGITIZER)` to query touch digitizer capabilities
- Decodes the bitmask to determine:
  - Whether integrated or external touch hardware exists
  - Whether the touch subsystem is ready
  - Maximum touch points supported

**Layer 3: Functional Test**
- Actually calls `InitializeTouchInjection()` to test initialization
- If successful, calls `InjectTouchInput()` with a test contact at (100, 100)
- Immediately sends a touch-up event to clean up
- Records error codes from any failures

### Diagnosis Logic

The function correlates hardware detection with functional test results:

- If `InjectTouchInput` fails with error 87 AND no touch digitizer detected:
  → "No touch digitizer detected... Touch injection requires touch hardware."
- If error 87 AND touch detected but not ready:
  → "Touch hardware detected but not ready..."
- If error 87 AND touch ready:
  → "Touch hardware present and ready, but injection failed..."
- If error 5:
  → "ERROR_ACCESS_DENIED... Run as Administrator."

**Note**: If the diagnostic injection succeeds, touch injection will be
initialized as a side effect (with `max_contacts=1`).

## PARAMETERS

This function takes no parameters.

## RETURN VALUE

Returns a dictionary containing diagnostic information:

### API Availability

| Key | Type | Description |
|-----|------|-------------|
| `api_available` | `bool` | Whether Touch Injection API functions are available |

### Touch Hardware Information

| Key | Type | Description |
|-----|------|-------------|
| `has_touch_digitizer` | `bool` | Whether touch hardware is detected |
| `digitizer_flags` | `int` | Raw value from `GetSystemMetrics(SM_DIGITIZER)` |
| `max_touch_points` | `int` | Maximum touch points supported by hardware |
| `integrated_touch` | `bool` | Has integrated touch digitizer |
| `external_touch` | `bool` | Has external touch digitizer |
| `touch_ready` | `bool` | Touch subsystem is ready |

### Initialization Test

| Key | Type | Description |
|-----|------|-------------|
| `init_works` | `bool` | Whether `InitializeTouchInjection()` succeeded |
| `init_error` | `int` | Win32 error code (0 if successful) |

### Injection Test

| Key | Type | Description |
|-----|------|-------------|
| `inject_works` | `bool` | Whether `InjectTouchInput()` succeeded |
| `inject_error` | `int` | Win32 error code (0 if successful) |

### Diagnosis

| Key | Type | Description |
|-----|------|-------------|
| `diagnosis` | `str` | Human-readable explanation of the results |

## ERRORS

This function does not raise exceptions. All errors are captured and
reported in the returned dictionary.

On non-Windows platforms, calling `diagnose()` raises `ImportError` because
the stub implementation is `_not_available`.

## EXAMPLES

### Basic Diagnostic Check

```python
import wintouch

if wintouch.is_available():
    diag = wintouch.diagnose()
    print(f"Touch injection works: {diag['inject_works']}")
    print(f"Diagnosis: {diag['diagnosis']}")
else:
    print("Touch injection not available (requires Windows 8+)")
```

### Detailed Diagnostic Report

```python
import wintouch

def print_diagnostics():
    """Print comprehensive touch injection diagnostics."""
    if not wintouch.is_available():
        print("Touch Injection API: NOT AVAILABLE")
        print("Requires Windows 8 or later")
        return

    diag = wintouch.diagnose()

    print("=== Touch Injection Diagnostics ===")
    print()
    print("API Status:")
    print(f"  API Available: {diag['api_available']}")
    print()
    print("Hardware Detection:")
    print(f"  Has Touch Digitizer: {diag['has_touch_digitizer']}")
    print(f"  Digitizer Flags: 0x{diag['digitizer_flags']:08x}")
    print(f"  Max Touch Points: {diag['max_touch_points']}")
    print(f"  Integrated Touch: {diag['integrated_touch']}")
    print(f"  External Touch: {diag['external_touch']}")
    print(f"  Touch Ready: {diag['touch_ready']}")
    print()
    print("Functional Tests:")
    print(f"  Initialize Works: {diag['init_works']}")
    if diag['init_error']:
        print(f"  Initialize Error: {diag['init_error']}")
    print(f"  Inject Works: {diag['inject_works']}")
    if diag['inject_error']:
        print(f"  Inject Error: {diag['inject_error']}")
    print()
    print("Diagnosis:")
    print(f"  {diag['diagnosis']}")

print_diagnostics()
```

### Error Handling Based on Diagnosis

```python
import wintouch
import sys

def setup_touch():
    """Set up touch injection with diagnostic error handling."""
    if not wintouch.is_available():
        print("Error: Touch injection requires Windows 8+", file=sys.stderr)
        return False

    diag = wintouch.diagnose()

    if diag['inject_works']:
        # diagnose() already initialized touch injection
        return True

    # Analyze the failure
    if diag['init_error'] == 5:  # ERROR_ACCESS_DENIED
        print("Error: Access denied. Try running as Administrator.", file=sys.stderr)
    elif diag['inject_error'] == 87:  # ERROR_INVALID_PARAMETER
        if not diag['has_touch_digitizer']:
            print("Error: No touch hardware detected.", file=sys.stderr)
            print("Touch injection may require touch hardware.", file=sys.stderr)
        else:
            print("Error: Touch injection failed.", file=sys.stderr)
            print(f"Details: {diag['diagnosis']}", file=sys.stderr)
    else:
        print(f"Error: {diag['diagnosis']}", file=sys.stderr)

    return False

if setup_touch():
    print("Touch injection ready!")
    # Continue with application
```

### JSON Output for Logging

```python
import wintouch
import json

def get_diagnostic_json():
    """Get diagnostics as JSON string."""
    if wintouch.is_available():
        diag = wintouch.diagnose()
    else:
        diag = {
            "api_available": False,
            "diagnosis": "Touch injection API not available (requires Windows 8+)"
        }

    return json.dumps(diag, indent=2)

print(get_diagnostic_json())
```

## NOTES

### Side Effect: Initialization

If `diagnose()` successfully injects a test touch event, it initializes
touch injection with `max_contacts=1` as a side effect. After a successful
`diagnose()`, you can immediately use `inject()`.

If you need more than 1 contact, call `initialize()` explicitly (in a new
process, as reinitialization is not possible).

### Digitizer Flags

The `digitizer_flags` value is the raw result from `GetSystemMetrics(SM_DIGITIZER)`.
Relevant bits:

| Flag | Value | Meaning |
|------|-------|---------|
| `NID_INTEGRATED_TOUCH` | `0x01` | Integrated touch digitizer |
| `NID_EXTERNAL_TOUCH` | `0x02` | External touch digitizer |
| `NID_MULTI_INPUT` | `0x40` | Multi-input digitizer |
| `NID_READY` | `0x80` | Touch digitizer is ready |

### Test Touch Event

The diagnostic injection sends a quick DOWN-UP sequence at coordinates
(100, 100). This may briefly trigger UI elements at that location. The
touch is immediately released.

### Touch Hardware Required

**Touch injection requires touch hardware.** If `has_touch_digitizer` is `False`,
touch injection will not work regardless of other settings. This is a Windows
limitation - the Touch Injection API does not function without a touch digitizer.

When `has_touch_digitizer` is `False`:
- `init_works` may still be `True` (initialization succeeds)
- `inject_works` will be `False` with error 87
- The `diagnosis` message will indicate the hardware requirement

### Error Codes Reference

Common Win32 error codes you may see:

| Code | Name | Typical Cause |
|------|------|---------------|
| 5 | ERROR_ACCESS_DENIED | Permission denied, or another process owns touch injection |
| 87 | ERROR_INVALID_PARAMETER | No touch hardware, or invalid touch data |

**Important**: Error 87 with touch injection typically indicates missing touch
hardware, not a programming error. Check `has_touch_digitizer` first.

### Performance

`diagnose()` is relatively slow as it makes multiple Windows API calls and
performs actual touch injection. Use it for initial capability checking,
not in performance-critical paths.

## SEE ALSO

- [initialize(3)](initialize.md) - Initialize touch injection
- [is_available(3)](is_available.md) - Quick availability check
- [inject(3)](inject.md) - Inject touch input events
- [GetSystemMetrics (MSDN)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getsystemmetrics)

## HISTORY

- **v0.1.0**: Initial implementation
