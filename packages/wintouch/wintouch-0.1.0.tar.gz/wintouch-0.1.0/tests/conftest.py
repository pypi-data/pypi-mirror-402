"""
Pytest configuration for wintouch tests.

Note: Touch injection tests require Administrator privileges on Windows.
Tests marked with @pytest.mark.requires_touch_injection will be skipped
if touch injection is not available (missing hardware, drivers, or privileges).
"""

import pytest
import wintouch


def can_inject_touch():
    """
    Check if touch injection actually works on this system.
    
    Touch injection may fail with ERROR_INVALID_PARAMETER (87) on systems
    that don't have touch hardware/drivers or when not running with proper
    privileges (Administrator or UIAccess).
    """
    if not wintouch.is_available():
        return False
    
    try:
        # Initialize if not already
        if not wintouch.is_initialized():
            wintouch.initialize(max_contacts=1)
        
        # Try a simple injection
        wintouch.inject([{
            "x": 100,
            "y": 100,
            "flags": wintouch.FLAGS_DOWN
        }])
        # Clean up
        wintouch.inject([{
            "x": 100,
            "y": 100,
            "flags": wintouch.FLAGS_UP
        }])
        return True
    except OSError:
        return False


# Check once at module load
_CAN_INJECT = None
_SKIP_REASON = None

def get_can_inject():
    global _CAN_INJECT, _SKIP_REASON
    if _CAN_INJECT is None:
        _CAN_INJECT = can_inject_touch()
        if not _CAN_INJECT:
            if not wintouch.is_available():
                _SKIP_REASON = "Touch injection API not available (requires Windows 8+)"
            else:
                _SKIP_REASON = (
                    "Touch injection failed (error 87). "
                    "Requires Administrator privileges or touch hardware/drivers. "
                    "Run pytest as Administrator to enable these tests."
                )
    return _CAN_INJECT


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_touch_injection: skip test if touch injection not available "
        "(requires touch hardware and Administrator privileges)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked with requires_touch_injection if not available."""
    if get_can_inject():
        return
    
    skip_touch = pytest.mark.skip(reason=_SKIP_REASON)
    for item in items:
        if "requires_touch_injection" in item.keywords:
            item.add_marker(skip_touch)
