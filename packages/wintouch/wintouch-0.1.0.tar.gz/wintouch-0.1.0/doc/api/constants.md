# constants(3) - wintouch

## NAME

constants - flag and mask constants for touch injection

## SYNOPSIS

```python
import wintouch

# Convenience flags
wintouch.FLAGS_DOWN
wintouch.FLAGS_UPDATE
wintouch.FLAGS_UP

# Pointer flags
wintouch.POINTER_FLAG_NONE
wintouch.POINTER_FLAG_DOWN
# ... etc

# Touch flags
wintouch.TOUCH_FLAG_NONE

# Touch masks
wintouch.TOUCH_MASK_NONE
wintouch.TOUCH_MASK_CONTACTAREA
# ... etc

# Feedback modes
wintouch.FEEDBACK_DEFAULT
wintouch.FEEDBACK_INDIRECT
wintouch.FEEDBACK_NONE
```

## DESCRIPTION

This document describes all constants exported by the wintouch module. These
constants are used to configure touch injection behavior and specify touch
event properties.

---

## CONVENIENCE FLAGS

Pre-built flag combinations for common touch operations. These are the
recommended way to specify touch state in the `flags` field of contact
dictionaries.

**WARNING**: Always use these convenience flags rather than combining raw
pointer flags yourself. The Windows Touch Injection API is extremely particular
about flag combinations. Adding seemingly reasonable flags like `POINTER_FLAG_PRIMARY`
or `POINTER_FLAG_CONFIDENCE` causes `ERROR_INVALID_PARAMETER` (87). These
convenience flags match Microsoft's official sample code exactly and are the
only combinations known to work reliably.

### FLAGS_DOWN

```python
wintouch.FLAGS_DOWN
```

**Value**: `0x00010006` (`POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT`)

**Description**: Use when a finger first contacts the screen. This combination
indicates that a new touch point has started, is within range of the digitizer,
and is actively touching the surface.

**Example**:
```python
wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
```

---

### FLAGS_UPDATE

```python
wintouch.FLAGS_UPDATE
```

**Value**: `0x00020006` (`POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT`)

**Description**: Use when a finger moves while still touching the screen. This
combination indicates a position update for an existing touch point that is
still in contact.

**Example**:
```python
wintouch.inject([{"x": 510, "y": 310, "flags": wintouch.FLAGS_UPDATE}])
```

---

### FLAGS_UP

```python
wintouch.FLAGS_UP
```

**Value**: `0x00040000` (`POINTER_FLAG_UP`)

**Description**: Use when a finger leaves the screen. This indicates the touch
point has ended. Unlike DOWN and UPDATE, UP does not include INRANGE or
INCONTACT flags.

**Example**:
```python
wintouch.inject([{"x": 510, "y": 310, "flags": wintouch.FLAGS_UP}])
```

---

## POINTER FLAGS

Raw pointer state flags from the Windows API.

**CAUTION**: Do not combine these flags yourself for touch injection. Use the
convenience flags (`FLAGS_DOWN`, `FLAGS_UPDATE`, `FLAGS_UP`) instead. Custom
flag combinations typically cause `ERROR_INVALID_PARAMETER` (87).

These constants are exported for completeness and for applications that need
to inspect or compare flag values, but they should not be used to construct
custom flag combinations for injection.

### POINTER_FLAG_NONE

```python
wintouch.POINTER_FLAG_NONE
```

**Value**: `0x00000000`

**Description**: No flags set. Rarely used directly.

---

### POINTER_FLAG_NEW

```python
wintouch.POINTER_FLAG_NEW
```

**Value**: `0x00000001`

**Description**: Indicates a new pointer input. The system automatically
sets this for new touch points.

---

### POINTER_FLAG_INRANGE

```python
wintouch.POINTER_FLAG_INRANGE
```

**Value**: `0x00000002`

**Description**: Pointer is within the digitizer's detection range. Used with
DOWN and UPDATE events when the finger is close enough to be tracked.

---

### POINTER_FLAG_INCONTACT

```python
wintouch.POINTER_FLAG_INCONTACT
```

**Value**: `0x00000004`

**Description**: Pointer is in physical contact with the surface. Used with
DOWN and UPDATE events when the finger is touching the screen.

---

### POINTER_FLAG_FIRSTBUTTON

```python
wintouch.POINTER_FLAG_FIRSTBUTTON
```

**Value**: `0x00000010`

**Description**: Primary button is pressed. For touch input, this typically
corresponds to a normal touch.

---

### POINTER_FLAG_PRIMARY

```python
wintouch.POINTER_FLAG_PRIMARY
```

**Value**: `0x00002000`

**Description**: This is the primary touch point. In multi-touch scenarios,
one contact is designated as primary for compatibility with applications
that only handle single-touch.

---

### POINTER_FLAG_CONFIDENCE

```python
wintouch.POINTER_FLAG_CONFIDENCE
```

**Value**: `0x00004000`

**Description**: High-confidence touch detection. Indicates the system is
confident in the validity of this touch point.

---

### POINTER_FLAG_CANCELED

```python
wintouch.POINTER_FLAG_CANCELED
```

**Value**: `0x00008000`

**Description**: Touch was canceled. Used when palm rejection or similar
logic invalidates a touch.

---

### POINTER_FLAG_DOWN

```python
wintouch.POINTER_FLAG_DOWN
```

**Value**: `0x00010000`

**Description**: Pointer transitioned to down state (contact began). Must be
combined with INRANGE and INCONTACT for normal touch down. Included in
`FLAGS_DOWN`.

---

### POINTER_FLAG_UPDATE

```python
wintouch.POINTER_FLAG_UPDATE
```

**Value**: `0x00020000`

**Description**: Pointer position or properties changed. Must be combined with
INRANGE and INCONTACT for normal touch move. Included in `FLAGS_UPDATE`.

---

### POINTER_FLAG_UP

```python
wintouch.POINTER_FLAG_UP
```

**Value**: `0x00040000`

**Description**: Pointer transitioned to up state (contact ended). Used alone
without INRANGE or INCONTACT. This is the `FLAGS_UP` value.

---

## TOUCH FLAGS

Touch-specific flags. Currently, only TOUCH_FLAG_NONE is defined.

### TOUCH_FLAG_NONE

```python
wintouch.TOUCH_FLAG_NONE
```

**Value**: `0x00000000`

**Description**: No touch-specific flags. This is the default value used
internally.

---

## TOUCH MASKS

Validity masks indicating which optional touch properties are set in a
contact. The C extension automatically sets appropriate masks based on
which optional fields are provided.

### TOUCH_MASK_NONE

```python
wintouch.TOUCH_MASK_NONE
```

**Value**: `0x00000000`

**Description**: No optional touch properties are valid.

---

### TOUCH_MASK_CONTACTAREA

```python
wintouch.TOUCH_MASK_CONTACTAREA
```

**Value**: `0x00000001`

**Description**: The contact area (rcContact rectangle) is valid. Automatically
set when `contact_width` or `contact_height` are specified.

---

### TOUCH_MASK_ORIENTATION

```python
wintouch.TOUCH_MASK_ORIENTATION
```

**Value**: `0x00000002`

**Description**: The orientation field is valid. Automatically set when
`orientation` is specified.

---

### TOUCH_MASK_PRESSURE

```python
wintouch.TOUCH_MASK_PRESSURE
```

**Value**: `0x00000004`

**Description**: The pressure field is valid. Automatically set when
`pressure` is specified.

---

## FEEDBACK MODES

Visual feedback configuration for touch injection. Passed to `initialize()`
as the `feedback_mode` parameter.

### FEEDBACK_DEFAULT

```python
wintouch.FEEDBACK_DEFAULT
```

**Value**: `0x1`

**Description**: Show default touch visualization. A small circle or indicator
appears at the touch point, providing visual feedback to users and developers.

**Example**:
```python
wintouch.initialize(feedback_mode=wintouch.FEEDBACK_DEFAULT)
```

---

### FEEDBACK_INDIRECT

```python
wintouch.FEEDBACK_INDIRECT
```

**Value**: `0x2`

**Description**: Indirect touch feedback mode. The exact behavior depends on
Windows version and configuration.

**Example**:
```python
wintouch.initialize(feedback_mode=wintouch.FEEDBACK_INDIRECT)
```

---

### FEEDBACK_NONE

```python
wintouch.FEEDBACK_NONE
```

**Value**: `0x3`

**Description**: No visual feedback. Touch events are injected silently without
any on-screen indicators. Useful for automated testing or when visual feedback
is undesirable.

**Example**:
```python
wintouch.initialize(feedback_mode=wintouch.FEEDBACK_NONE)
```

---

## COMBINING FLAGS

For advanced use cases, raw pointer flags can be combined:

```python
import wintouch

# Custom combination example (equivalent to FLAGS_DOWN + PRIMARY)
custom_down = (
    wintouch.POINTER_FLAG_DOWN |
    wintouch.POINTER_FLAG_INRANGE |
    wintouch.POINTER_FLAG_INCONTACT |
    wintouch.POINTER_FLAG_PRIMARY
)

wintouch.inject([{"x": 500, "y": 300, "flags": custom_down}])
```

**Note**: The convenience flags (`FLAGS_DOWN`, `FLAGS_UPDATE`, `FLAGS_UP`) are
sufficient for most applications. Use raw flags only when specific behavior
is required.

---

## CONSTANT VALUES REFERENCE

| Constant | Hex Value | Decimal |
|----------|-----------|---------|
| `FLAGS_DOWN` | `0x00010006` | 65542 |
| `FLAGS_UPDATE` | `0x00020006` | 131078 |
| `FLAGS_UP` | `0x00040000` | 262144 |
| `POINTER_FLAG_NONE` | `0x00000000` | 0 |
| `POINTER_FLAG_NEW` | `0x00000001` | 1 |
| `POINTER_FLAG_INRANGE` | `0x00000002` | 2 |
| `POINTER_FLAG_INCONTACT` | `0x00000004` | 4 |
| `POINTER_FLAG_FIRSTBUTTON` | `0x00000010` | 16 |
| `POINTER_FLAG_PRIMARY` | `0x00002000` | 8192 |
| `POINTER_FLAG_CONFIDENCE` | `0x00004000` | 16384 |
| `POINTER_FLAG_CANCELED` | `0x00008000` | 32768 |
| `POINTER_FLAG_DOWN` | `0x00010000` | 65536 |
| `POINTER_FLAG_UPDATE` | `0x00020000` | 131072 |
| `POINTER_FLAG_UP` | `0x00040000` | 262144 |
| `TOUCH_FLAG_NONE` | `0x00000000` | 0 |
| `TOUCH_MASK_NONE` | `0x00000000` | 0 |
| `TOUCH_MASK_CONTACTAREA` | `0x00000001` | 1 |
| `TOUCH_MASK_ORIENTATION` | `0x00000002` | 2 |
| `TOUCH_MASK_PRESSURE` | `0x00000004` | 4 |
| `FEEDBACK_DEFAULT` | `0x00000001` | 1 |
| `FEEDBACK_INDIRECT` | `0x00000002` | 2 |
| `FEEDBACK_NONE` | `0x00000003` | 3 |

---

## SEE ALSO

- [inject(3)](inject.md) - Inject touch input events
- [initialize(3)](initialize.md) - Initialize touch injection
- [INDEX](INDEX.md) - API index
- [POINTER_FLAGS (MSDN)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ne-winuser-pointer_flags)

## HISTORY

- **v0.1.0**: Initial implementation
