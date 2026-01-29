# is_initialized(3) - wintouch

## NAME

is_initialized - check if touch injection has been initialized

## SYNOPSIS

```python
import wintouch

initialized = wintouch.is_initialized()
```

## DESCRIPTION

The `is_initialized()` function checks whether the touch injection subsystem
has been successfully initialized in the current process. This function
queries the module's internal state without making any Windows API calls.

Use this function to check if `initialize()` has been called before
attempting to inject touch events.

## PARAMETERS

This function takes no parameters.

## RETURN VALUE

Returns `True` if touch injection has been initialized (either by calling
`initialize()` or as a side effect of `diagnose()` succeeding).

Returns `False` if touch injection has not been initialized.

## ERRORS

This function does not raise exceptions.

On non-Windows platforms, the stub implementation always returns `False`.

## EXAMPLES

### Check Before Injection

```python
import wintouch

def tap(x, y):
    """Perform a tap, initializing if needed."""
    if not wintouch.is_initialized():
        wintouch.initialize()

    wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_DOWN}])
    wintouch.inject([{"x": x, "y": y, "flags": wintouch.FLAGS_UP}])

tap(500, 300)
```

### Status Report

```python
import wintouch

def print_status():
    """Print current touch injection status."""
    print(f"API Available: {wintouch.is_available()}")
    print(f"Initialized: {wintouch.is_initialized()}")
    if wintouch.is_initialized():
        print(f"Max Contacts: {wintouch.get_max_contacts()}")

print_status()
# Output:
# API Available: True
# Initialized: False

wintouch.initialize(max_contacts=3)
print_status()
# Output:
# API Available: True
# Initialized: True
# Max Contacts: 3
```

### Singleton Initialization Pattern

```python
import wintouch

_initialized = False

def ensure_initialized(max_contacts=2):
    """Ensure touch injection is initialized exactly once."""
    global _initialized
    if not _initialized and not wintouch.is_initialized():
        wintouch.initialize(max_contacts=max_contacts)
        _initialized = True

# Can be called multiple times safely
ensure_initialized()
ensure_initialized()
ensure_initialized()  # No effect, already initialized
```

### Conditional Execution

```python
import wintouch

def perform_touch_operation():
    """Execute only if touch is ready."""
    if not wintouch.is_available():
        raise RuntimeError("Touch injection not available")

    if not wintouch.is_initialized():
        raise RuntimeError("Touch injection not initialized")

    # Safe to inject
    wintouch.inject([{"x": 100, "y": 100, "flags": wintouch.FLAGS_DOWN}])
    wintouch.inject([{"x": 100, "y": 100, "flags": wintouch.FLAGS_UP}])
```

## NOTES

### State Persistence

Once initialized, touch injection remains active for the lifetime of the
process. There is no way to uninitialize or reset the state without
restarting the process. Therefore, `is_initialized()` will return `True`
from the first successful initialization until process exit.

### Interaction with diagnose()

The `diagnose()` function internally attempts touch injection as part of
its diagnostics. If the diagnostic injection succeeds, it sets the internal
initialized state to `True`. This means:

```python
import wintouch

print(wintouch.is_initialized())  # False

diag = wintouch.diagnose()
if diag['inject_works']:
    print(wintouch.is_initialized())  # True (side effect of diagnose)
```

### Thread Safety

This function reads a single boolean flag and is safe to call from multiple
threads.

### Relation to is_available()

- `is_available()` - Checks if the API exists (can we try to initialize?)
- `is_initialized()` - Checks if we have initialized (can we inject?)

Typical flow:
```python
if wintouch.is_available():      # API exists?
    if not wintouch.is_initialized():  # Not yet initialized?
        wintouch.initialize()           # Initialize
    wintouch.inject(...)                # Use
```

## SEE ALSO

- [initialize(3)](initialize.md) - Initialize touch injection
- [is_available(3)](is_available.md) - Check API availability
- [get_max_contacts(3)](get_max_contacts.md) - Get configured max contacts
- [diagnose(3)](diagnose.md) - Comprehensive capability diagnosis

## HISTORY

- **v0.1.0**: Initial implementation
