# initialize(3) - wintouch

## NAME

initialize - initialize the Windows Touch Injection subsystem

## SYNOPSIS

```python
import wintouch

wintouch.initialize(max_contacts=1, feedback_mode=wintouch.FEEDBACK_DEFAULT)
```

## DESCRIPTION

The `initialize()` function initializes the Windows Touch Injection subsystem,
preparing it to accept injected touch input events. This function must be
called before any calls to `inject()`.

Touch injection initialization is a system-wide resource. Only one process
can have touch injection initialized at any given time. If another process
has already initialized touch injection, this call will fail.

Once initialized, the touch injection subsystem remains active until the
process exits. There is no corresponding "uninitialize" function in the
Windows API.

## PARAMETERS

**max_contacts** (`int`, optional)
: The maximum number of simultaneous touch contacts that can be injected.
  Valid range is 1 to 10 inclusive. Default value is `1`.

  This value determines how many touch points can be active at the same time.
  For single-finger operations, `1` is sufficient. For multi-touch gestures
  like pinch-to-zoom or rotation, use `2` or more.

**feedback_mode** (`int`, optional)
: The visual feedback mode for touch injection. Controls whether and how
  touch visualizations are displayed on screen. Default is `FEEDBACK_DEFAULT`.

  Available modes:

  | Constant | Value | Description |
  |----------|-------|-------------|
  | `FEEDBACK_DEFAULT` | `0x1` | Show standard touch visualization circles |
  | `FEEDBACK_INDIRECT` | `0x2` | Show indirect touch feedback |
  | `FEEDBACK_NONE` | `0x3` | No visual feedback |

## RETURN VALUE

Returns `True` on successful initialization.

## ERRORS

**ValueError**
: Raised if `max_contacts` is less than 1 or greater than 10.

**OSError**
: Raised if the Windows API call `InitializeTouchInjection()` fails.
  The error message includes the Win32 error code.

  Common error codes:

  | Code | Name | Cause |
  |------|------|-------|
  | 5 | ERROR_ACCESS_DENIED | Another process owns touch injection, or insufficient privileges |
  | 87 | ERROR_INVALID_PARAMETER | Invalid parameter (rare with Python wrapper validation) |

## EXAMPLES

### Basic Initialization

```python
import wintouch

# Initialize with defaults (1 contact, default feedback)
wintouch.initialize()

# Now ready to inject touch events
wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
```

### Multi-touch Initialization

```python
import wintouch

# Initialize for two-finger gestures
wintouch.initialize(max_contacts=2)

# Pinch gesture
wintouch.inject([
    {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
])
```

### Silent Initialization (No Visual Feedback)

```python
import wintouch

# Initialize without touch visualization
wintouch.initialize(max_contacts=1, feedback_mode=wintouch.FEEDBACK_NONE)

# Touch events will be injected without visual indicators
```

### Error Handling

```python
import wintouch

try:
    wintouch.initialize(max_contacts=5)
except OSError as e:
    if "error 5" in str(e):
        print("Access denied. Try running as Administrator.")
        print("Or another process may have touch injection active.")
    else:
        print(f"Initialization failed: {e}")
except ValueError as e:
    print(f"Invalid parameter: {e}")
```

### Checking Before Initialization

```python
import wintouch

# Check availability first
if not wintouch.is_available():
    print("Touch injection requires Windows 8 or later")
    exit(1)

# Check if already initialized
if wintouch.is_initialized():
    print(f"Already initialized with {wintouch.get_max_contacts()} contacts")
else:
    wintouch.initialize(max_contacts=2)
```

## NOTES

### Process Exclusivity

The Windows Touch Injection API allows only one process to own touch injection
at any time. If your application fails to initialize, another process may have
already claimed touch injection.

### Persistence

Once initialized, touch injection remains active for the lifetime of the
process. There is no way to release touch injection ownership or reinitialize
with different parameters without restarting the process.

### Calling Multiple Times

Calling `initialize()` multiple times in the same process will succeed, but
each call to `InitializeTouchInjection()` returns success without changing
the existing configuration. To change `max_contacts`, restart the process.

### Administrator Privileges

While not strictly required on all systems, running as Administrator may be
necessary on some configurations, particularly when other security software
is present.

### Interaction with diagnose()

The `diagnose()` function internally calls `InitializeTouchInjection()` as
part of its diagnostic tests. If `diagnose()` succeeds, it will have already
initialized touch injection with `max_contacts=1`.

## SEE ALSO

- [inject(3)](inject.md) - Inject touch input events
- [is_available(3)](is_available.md) - Check API availability
- [is_initialized(3)](is_initialized.md) - Check initialization state
- [get_max_contacts(3)](get_max_contacts.md) - Get configured max contacts
- [diagnose(3)](diagnose.md) - Comprehensive capability diagnosis
- [constants](constants.md) - Feedback mode constants
- [InitializeTouchInjection (MSDN)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-initializetouchinjection)

## HISTORY

- **v0.1.0**: Initial implementation
