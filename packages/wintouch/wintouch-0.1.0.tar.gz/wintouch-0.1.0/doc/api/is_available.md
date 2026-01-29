# is_available(3) - wintouch

## NAME

is_available - check if the Windows Touch Injection API is available

## SYNOPSIS

```python
import wintouch

available = wintouch.is_available()
```

## DESCRIPTION

The `is_available()` function checks whether the Windows Touch Injection API
is present and accessible on the current system. This function performs a
lightweight check by attempting to load the required functions from user32.dll.

**Important**: This function only checks if the API *exists* (Windows 8+), NOT
whether touch injection will actually work. Touch injection also requires:
- Touch hardware (integrated or external digitizer)
- Appropriate permissions

Use `diagnose()` for a comprehensive check that tests actual functionality.

This function does not require initialization and can be called at any time.
It is useful for early detection of unsupported systems before attempting
to initialize touch injection.

## PARAMETERS

This function takes no parameters.

## RETURN VALUE

Returns `True` if the Touch Injection API is available on this system.

Returns `False` if the API is not available, which typically means:
- Windows version is older than Windows 8
- The `InitializeTouchInjection` or `InjectTouchInput` functions could not
  be found in user32.dll

## ERRORS

This function does not raise exceptions. It catches all internal errors and
returns `False` if any problems occur during the availability check.

On non-Windows platforms where the C extension could not be imported, this
function returns `False` (via the stub implementation).

## EXAMPLES

### Basic Availability Check

```python
import wintouch

if wintouch.is_available():
    print("Touch injection is available")
    wintouch.initialize()
else:
    print("Touch injection requires Windows 8 or later")
```

### Guard Clause Pattern

```python
import wintouch
import sys

def main():
    if not wintouch.is_available():
        print("Error: Touch injection not available", file=sys.stderr)
        print("This application requires Windows 8 or later", file=sys.stderr)
        sys.exit(1)

    wintouch.initialize()
    # ... rest of application

if __name__ == "__main__":
    main()
```

### Conditional Feature Enable

```python
import wintouch

class InputManager:
    def __init__(self):
        self.touch_enabled = wintouch.is_available()
        if self.touch_enabled:
            wintouch.initialize(max_contacts=2)

    def tap(self, x, y):
        if self.touch_enabled:
            wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_DOWN}])
            wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_UP}])
        else:
            # Fallback to mouse simulation
            self._mouse_click(x, y)
```

### Combined with diagnose() for Detailed Check

```python
import wintouch

if wintouch.is_available():
    # API is available, but does it actually work?
    diag = wintouch.diagnose()
    if diag['inject_works']:
        print("Touch injection is fully functional")
    else:
        print(f"Touch injection available but not working: {diag['diagnosis']}")
else:
    print("Touch injection API not available (requires Windows 8+)")
```

## NOTES

### Caching Behavior

The availability check loads user32.dll and resolves function pointers on
first call. Subsequent calls return immediately using the cached result.
This makes the function very fast after the first call.

### Availability vs. Functionality

`is_available()` returning `True` indicates the API functions exist, but
does not guarantee that touch injection will succeed. Factors that can
prevent injection despite availability:

- No touch hardware present (required on some systems)
- Insufficient permissions
- Another process owns touch injection
- System configuration issues

Use `diagnose()` for a comprehensive check of actual functionality.

### Non-Windows Platforms

On non-Windows platforms (Linux, macOS), the C extension is not built or
cannot be imported. In this case, the Python wrapper provides a stub
`is_available()` function that always returns `False`.

```python
# On Linux/macOS:
>>> import wintouch
>>> wintouch.is_available()
False
```

### Thread Safety

This function is safe to call from multiple threads. The internal loading
is performed once with no concurrency issues.

## SEE ALSO

- [initialize(3)](initialize.md) - Initialize touch injection
- [diagnose(3)](diagnose.md) - Comprehensive capability diagnosis
- [is_initialized(3)](is_initialized.md) - Check initialization state

## HISTORY

- **v0.1.0**: Initial implementation
