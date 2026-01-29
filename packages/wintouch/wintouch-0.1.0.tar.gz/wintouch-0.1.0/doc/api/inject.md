# inject(3) - wintouch

## NAME

inject - inject touch input events into the system

## SYNOPSIS

```python
import wintouch

wintouch.inject(contacts)
```

## DESCRIPTION

The `inject()` function injects one or more touch contact events into the
Windows input system. These events are indistinguishable from actual touch
input from hardware and will be processed by the foreground application.

Touch injection must be initialized via `initialize()` before calling this
function. The number of contacts in a single call must not exceed the
`max_contacts` value specified during initialization.

Each contact in the list represents a single touch point with its position,
state flags, and optional properties like pressure and orientation.

## PARAMETERS

**contacts** (`list[dict]`)
: A list of contact dictionaries. Each dictionary represents one touch
  contact and must contain the required fields. The list must not be empty
  and must not contain more elements than the configured `max_contacts`.

### Contact Dictionary Fields

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `x` | `int` | X coordinate in screen pixels (from left edge) |
| `y` | `int` | Y coordinate in screen pixels (from top edge) |
| `flags` | `int` | Pointer flags indicating touch state (use convenience flags) |

#### Optional Fields

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `pointer_id` | `int` | List index | 0 to max_contacts-1 | Unique identifier for this contact |
| `pressure` | `int` | 32000 | 0-32000 | Pressure value (higher = more pressure) |
| `orientation` | `int` | 90 | 0-359 | Orientation in degrees from vertical |
| `contact_width` | `int` | 4 | >0 | Width of contact area in pixels |
| `contact_height` | `int` | 4 | >0 | Height of contact area in pixels |

### Flag Values

Use the convenience flag constants for common operations:

| Constant | Description | When to use |
|----------|-------------|-------------|
| `FLAGS_DOWN` | Finger contacts screen | Start of touch |
| `FLAGS_UPDATE` | Finger moves while touching | During drag/swipe |
| `FLAGS_UP` | Finger leaves screen | End of touch |

See [constants.md](constants.md) for raw pointer flags if needed.

## RETURN VALUE

Returns `True` on successful injection.

## ERRORS

**RuntimeError**
: Raised if touch injection has not been initialized. Call `initialize()` first.

**TypeError**
: Raised if `contacts` is not a list, or if a contact is not a dictionary.

**ValueError**
: Raised if `contacts` is empty, or if it contains more contacts than
  the configured `max_contacts`.

**KeyError**
: Raised if a required field (`x`, `y`, or `flags`) is missing from a contact.

**OSError**
: Raised if the Windows API call `InjectTouchInput()` fails.
  The error message includes the Win32 error code.

  Common error codes:

  | Code | Name | Cause |
  |------|------|-------|
  | 5 | ERROR_ACCESS_DENIED | Permission denied |
  | 87 | ERROR_INVALID_PARAMETER | Invalid data or no touch hardware |

## EXAMPLES

### Single Tap

```python
import wintouch

wintouch.initialize()

# Tap at coordinates (500, 300)
wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_UP}])
```

### Drag Gesture

```python
import wintouch
import time

wintouch.initialize()

# Start drag at (200, 300)
wintouch.inject([{"x": 200, "y": 300, "flags": wintouch.FLAGS_DOWN}])

# Move in steps
for x in range(250, 600, 50):
    wintouch.inject([{"x": x, "y": 300, "flags": wintouch.FLAGS_UPDATE}])
    time.sleep(0.02)

# End drag at (600, 300)
wintouch.inject([{"x": 600, "y": 300, "flags": wintouch.FLAGS_UP}])
```

### Multi-touch Pinch

```python
import wintouch
import time

wintouch.initialize(max_contacts=2)

# Two fingers down
wintouch.inject([
    {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
])

# Move fingers closer (pinch in)
for i in range(10):
    offset = 100 - i * 10
    wintouch.inject([
        {"x": 500 - offset, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
        {"x": 500 + offset, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
    ])
    time.sleep(0.02)

# Both fingers up
wintouch.inject([
    {"x": 490, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
    {"x": 510, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
])
```

### Touch with Pressure and Orientation

```python
import wintouch

wintouch.initialize()

# Heavy press (high pressure)
wintouch.inject([{
    "x": 500,
    "y": 300,
    "flags": wintouch.FLAGS_DOWN,
    "pressure": 30000,       # Near maximum
    "orientation": 45,       # Angled touch
    "contact_width": 20,     # Large contact area
    "contact_height": 15,
}])

# Light press (low pressure)
wintouch.inject([{
    "x": 500,
    "y": 300,
    "flags": wintouch.FLAGS_UPDATE,
    "pressure": 5000,        # Light touch
}])

wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_UP}])
```

### Error Handling

```python
import wintouch

try:
    wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
except RuntimeError as e:
    print("Not initialized:", e)
    wintouch.initialize()
    wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
except OSError as e:
    if "error 87" in str(e):
        print("Invalid parameter - touch hardware may be required")
    else:
        print(f"Injection failed: {e}")
```

### Complete Touch Sequence Helper

```python
import wintouch
import time

def touch_sequence(x, y, hold_time=0.0):
    """
    Perform a complete touch down-hold-up sequence.

    Args:
        x: X coordinate
        y: Y coordinate
        hold_time: Time to hold before releasing (seconds)
    """
    wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_DOWN}])
    if hold_time > 0:
        time.sleep(hold_time)
    wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_UP}])

# Usage
wintouch.initialize()
touch_sequence(500, 300)              # Quick tap
touch_sequence(500, 300, hold_time=1.0)  # Long press
```

## NOTES

### Coordinate System

Coordinates are in screen pixels with (0, 0) at the top-left corner of the
primary display. Multi-monitor setups may have negative coordinates for
displays to the left of or above the primary display.

### Contact Lifecycle

Each touch contact follows a lifecycle:

1. **DOWN**: Contact begins (`FLAGS_DOWN`)
2. **UPDATE**: Contact moves (zero or more `FLAGS_UPDATE` events)
3. **UP**: Contact ends (`FLAGS_UP`)

Each contact must go through this complete lifecycle. Failing to send an UP
event may leave the system in an inconsistent state.

### Pointer IDs

When using multiple contacts, each must have a unique `pointer_id`. The
default behavior assigns the list index as the pointer ID, which works for
most cases. Explicitly set `pointer_id` when:

- Contact IDs need to persist across inject calls
- Contacts are removed/added mid-gesture
- Specific ID values are required by the application

### Performance

Each `inject()` call makes a Win32 API call. For high-frequency injection:

- Batch all contacts in a single call when possible
- Consider timing carefully to avoid overwhelming the input system
- Typical applications work well with 30-60 inject calls per second

### Touch Hardware Requirement

**Touch injection requires touch hardware.** The Windows Touch Injection API
does not work on systems without a touch digitizer. This is a Windows
limitation, not a limitation of this library.

Use `diagnose()` to check if injection will work on the current system.
The `has_touch_digitizer` field indicates whether touch hardware is present.

### Coordinate Bounds

Coordinates must be within actual screen bounds. Injecting touch at coordinates
beyond the screen resolution (e.g., 10000x10000 on a 1920x1080 screen) causes
`ERROR_INVALID_PARAMETER` (87).

### Use Convenience Flags

Always use the provided convenience flags (`FLAGS_DOWN`, `FLAGS_UPDATE`, `FLAGS_UP`)
rather than combining raw pointer flags. The Windows API is very particular about
flag combinations - adding extra flags like `POINTER_FLAG_PRIMARY` or
`POINTER_FLAG_CONFIDENCE` causes `ERROR_INVALID_PARAMETER` even though they
seem reasonable.

## SEE ALSO

- [initialize(3)](initialize.md) - Initialize touch injection
- [is_initialized(3)](is_initialized.md) - Check initialization state
- [get_max_contacts(3)](get_max_contacts.md) - Get configured max contacts
- [constants](constants.md) - Flag constants
- [diagnose(3)](diagnose.md) - Diagnose touch capabilities
- [InjectTouchInput (MSDN)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-injecttouchinput)
- [POINTER_TOUCH_INFO (MSDN)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-pointer_touch_info)

## HISTORY

- **v0.1.0**: Initial implementation
