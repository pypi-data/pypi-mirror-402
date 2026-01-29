# get_max_contacts(3) - wintouch

## NAME

get_max_contacts - get the maximum number of configured simultaneous touch contacts

## SYNOPSIS

```python
import wintouch

max_contacts = wintouch.get_max_contacts()
```

## DESCRIPTION

The `get_max_contacts()` function returns the maximum number of simultaneous
touch contacts that were configured during initialization. This value was
specified as the `max_contacts` parameter to `initialize()`.

This function queries the module's internal state without making Windows
API calls.

## PARAMETERS

This function takes no parameters.

## RETURN VALUE

Returns an integer representing the maximum number of simultaneous touch
contacts allowed.

Returns `0` if touch injection has not been initialized.

## ERRORS

This function does not raise exceptions.

On non-Windows platforms, the stub implementation always returns `0`.

## EXAMPLES

### Basic Usage

```python
import wintouch

wintouch.initialize(max_contacts=5)
print(f"Configured for {wintouch.get_max_contacts()} contacts")
# Output: Configured for 5 contacts
```

### Check Before Multi-touch

```python
import wintouch

def pinch(center_x, center_y, start_distance, end_distance):
    """Perform a pinch gesture (requires 2 contacts)."""
    if wintouch.get_max_contacts() < 2:
        raise RuntimeError(
            f"Pinch requires 2 contacts, but only "
            f"{wintouch.get_max_contacts()} configured"
        )

    # ... perform pinch gesture ...

# This would fail:
wintouch.initialize(max_contacts=1)
try:
    pinch(500, 400, 200, 50)
except RuntimeError as e:
    print(e)  # Pinch requires 2 contacts, but only 1 configured

# This would work:
# (Note: Can't reinitialize in same process, this is illustrative)
# wintouch.initialize(max_contacts=2)
# pinch(500, 400, 200, 50)
```

### Dynamic Contact Allocation

```python
import wintouch

def inject_contacts(contacts):
    """
    Inject contacts, validating count against max_contacts.

    Args:
        contacts: List of contact dictionaries
    """
    max_allowed = wintouch.get_max_contacts()
    if len(contacts) > max_allowed:
        raise ValueError(
            f"Cannot inject {len(contacts)} contacts "
            f"(max is {max_allowed})"
        )

    wintouch.inject(contacts)

wintouch.initialize(max_contacts=3)
inject_contacts([
    {"x": 100, "y": 100, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 200, "y": 100, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
    {"x": 300, "y": 100, "pointer_id": 2, "flags": wintouch.FLAGS_DOWN},
])  # OK

inject_contacts([
    {"x": 100, "y": 100, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
    {"x": 200, "y": 100, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
    {"x": 300, "y": 100, "pointer_id": 2, "flags": wintouch.FLAGS_DOWN},
    {"x": 400, "y": 100, "pointer_id": 3, "flags": wintouch.FLAGS_DOWN},
])  # Raises ValueError
```

### Status Reporting

```python
import wintouch

def get_touch_status():
    """Return comprehensive touch injection status."""
    return {
        "available": wintouch.is_available(),
        "initialized": wintouch.is_initialized(),
        "max_contacts": wintouch.get_max_contacts(),
    }

print(get_touch_status())
# Before init: {'available': True, 'initialized': False, 'max_contacts': 0}

wintouch.initialize(max_contacts=2)
print(get_touch_status())
# After init: {'available': True, 'initialized': True, 'max_contacts': 2}
```

## NOTES

### Return Value Before Initialization

If touch injection has not been initialized, this function returns `0`.
This can be used to check initialization state:

```python
if wintouch.get_max_contacts() == 0:
    # Not initialized (or stub on non-Windows)
    pass
```

However, `is_initialized()` is the preferred way to check initialization.

### Immutable After Initialization

The `max_contacts` value is set during `initialize()` and cannot be changed
without restarting the process. Windows does not provide a way to
reinitialize touch injection with different parameters.

### Relation to inject() Validation

The `inject()` function validates that the contact list does not exceed
`max_contacts`. You can use `get_max_contacts()` to perform the same
validation before calling inject, providing custom error messages.

### Thread Safety

This function reads a single integer value and is safe to call from multiple
threads.

## SEE ALSO

- [initialize(3)](initialize.md) - Initialize touch injection
- [inject(3)](inject.md) - Inject touch input events
- [is_initialized(3)](is_initialized.md) - Check initialization state

## HISTORY

- **v0.1.0**: Initial implementation
