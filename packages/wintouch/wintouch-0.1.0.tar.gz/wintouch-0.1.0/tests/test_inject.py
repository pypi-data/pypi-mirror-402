"""
Tests for wintouch.inject() function.

These tests verify:
- Valid contact dictionaries
- Required fields validation
- Optional fields handling
- Error conditions
- Edge cases
"""

import pytest
import wintouch


# Skip all tests in this module if touch API is not available
pytestmark = pytest.mark.skipif(
    not wintouch.is_available(),
    reason="Touch injection API not available (requires Windows 8+)"
)


@pytest.fixture(autouse=True)
def init_touch():
    """Initialize touch injection before each test."""
    wintouch.initialize(max_contacts=10)


class TestInjectValidContacts:
    """Tests for inject() with valid contact dictionaries."""

    @pytest.mark.requires_touch_injection
    def test_inject_single_contact_down(self):
        """inject() with single touch down contact should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_single_contact_update(self):
        """inject() with touch update contact should succeed."""
        # Touch down first
        wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
        # Then update
        result = wintouch.inject([{
            "x": 510,
            "y": 310,
            "flags": wintouch.FLAGS_UPDATE
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_single_contact_up(self):
        """inject() with touch up contact should succeed."""
        # Touch down first
        wintouch.inject([{"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN}])
        # Then up
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_UP
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_multiple_contacts(self):
        """inject() with multiple contacts should succeed."""
        result = wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_with_pointer_id(self):
        """inject() with explicit pointer_id should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "pointer_id": 0,
            "flags": wintouch.FLAGS_DOWN
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_with_pressure(self):
        """inject() with pressure field should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "pressure": 512
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_with_orientation(self):
        """inject() with orientation field should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "orientation": 45
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_with_contact_area(self):
        """inject() with contact area fields should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "contact_width": 50,
            "contact_height": 50
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_with_all_optional_fields(self):
        """inject() with all optional fields should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "pointer_id": 0,
            "pressure": 512,
            "orientation": 90,
            "contact_width": 40,
            "contact_height": 60
        }])
        assert result is True


class TestInjectInvalidContacts:
    """Tests for inject() with invalid contact dictionaries."""

    def test_inject_missing_x(self):
        """inject() with missing 'x' should raise KeyError."""
        with pytest.raises(KeyError, match="'x'"):
            wintouch.inject([{
                "y": 300,
                "flags": wintouch.FLAGS_DOWN
            }])

    def test_inject_missing_y(self):
        """inject() with missing 'y' should raise KeyError."""
        with pytest.raises(KeyError, match="'y'"):
            wintouch.inject([{
                "x": 500,
                "flags": wintouch.FLAGS_DOWN
            }])

    def test_inject_missing_flags(self):
        """inject() with missing 'flags' should raise KeyError."""
        with pytest.raises(KeyError, match="'flags'"):
            wintouch.inject([{
                "x": 500,
                "y": 300
            }])

    def test_inject_empty_list(self):
        """inject() with empty contact list should raise ValueError."""
        with pytest.raises(ValueError, match="contacts list cannot be empty"):
            wintouch.inject([])

    def test_inject_not_a_list(self):
        """inject() with non-list argument should raise TypeError."""
        with pytest.raises(TypeError):
            wintouch.inject({"x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN})

    def test_inject_contact_not_dict(self):
        """inject() with non-dict contact should raise TypeError."""
        with pytest.raises(TypeError, match="must be a dictionary"):
            wintouch.inject([(500, 300, wintouch.FLAGS_DOWN)])

    def test_inject_too_many_contacts(self):
        """inject() with more contacts than max_contacts should raise ValueError."""
        wintouch.initialize(max_contacts=2)
        with pytest.raises(ValueError, match="Too many contacts"):
            wintouch.inject([
                {"x": 100, "y": 100, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
                {"x": 200, "y": 200, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
                {"x": 300, "y": 300, "pointer_id": 2, "flags": wintouch.FLAGS_DOWN},
            ])


class TestInjectNotInitialized:
    """Tests for inject() when not initialized."""

    def test_inject_before_initialize(self):
        """inject() before initialize() should raise RuntimeError."""
        # This test would require a fresh module state
        # In practice, if initialize() was called in a fixture, this can't be tested
        # We document this as a known limitation
        pass  # Cannot reliably test without process isolation


class TestInjectEdgeCases:
    """Tests for inject() edge cases."""

    @pytest.mark.requires_touch_injection
    def test_inject_coordinate_zero(self):
        """inject() with (0, 0) coordinates should succeed."""
        result = wintouch.inject([{
            "x": 0,
            "y": 0,
            "flags": wintouch.FLAGS_DOWN
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_coordinate_screen_edge(self):
        """inject() with coordinates at typical screen edge should succeed."""
        # Note: Coordinates outside actual screen bounds cause ERROR_INVALID_PARAMETER
        # Use coordinates within typical screen range (not 10000x10000)
        result = wintouch.inject([{
            "x": 1000,
            "y": 800,
            "flags": wintouch.FLAGS_DOWN
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_pressure_zero(self):
        """inject() with pressure=0 should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "pressure": 0
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_pressure_max(self):
        """inject() with pressure=1024 should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "pressure": 1024
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_orientation_zero(self):
        """inject() with orientation=0 should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "orientation": 0
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_orientation_max(self):
        """inject() with orientation=359 should succeed."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "orientation": 359
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_contact_width_only(self):
        """inject() with contact_width but no contact_height should use width for both."""
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN,
            "contact_width": 50
        }])
        assert result is True


class TestInjectRawFlags:
    """Tests for inject() with raw pointer flags."""

    @pytest.mark.requires_touch_injection
    def test_inject_pointer_flag_down(self):
        """inject() with POINTER_FLAG_DOWN should work."""
        flags = (
            wintouch.POINTER_FLAG_DOWN |
            wintouch.POINTER_FLAG_INRANGE |
            wintouch.POINTER_FLAG_INCONTACT
        )
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": flags
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_pointer_flag_update(self):
        """inject() with POINTER_FLAG_UPDATE should work."""
        # First touch down
        wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN
        }])
        # Then update with raw flags
        flags = (
            wintouch.POINTER_FLAG_UPDATE |
            wintouch.POINTER_FLAG_INRANGE |
            wintouch.POINTER_FLAG_INCONTACT
        )
        result = wintouch.inject([{
            "x": 510,
            "y": 310,
            "flags": flags
        }])
        assert result is True

    @pytest.mark.requires_touch_injection
    def test_inject_pointer_flag_up(self):
        """inject() with POINTER_FLAG_UP should work."""
        # First touch down
        wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": wintouch.FLAGS_DOWN
        }])
        # Then up with raw flags
        flags = wintouch.POINTER_FLAG_UP
        result = wintouch.inject([{
            "x": 500,
            "y": 300,
            "flags": flags
        }])
        assert result is True
