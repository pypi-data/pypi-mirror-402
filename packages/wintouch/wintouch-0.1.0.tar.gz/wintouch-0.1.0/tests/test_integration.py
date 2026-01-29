"""
Integration tests for wintouch - complete touch sequences.

These tests verify:
- Single touch tap sequence
- Single touch drag sequence
- Multi-touch pinch gesture
- Multi-touch tap sequence
- Complex touch sequences

Note: These tests require actual touch injection capability.
They will be skipped on systems without touch hardware/drivers
or when not running with proper privileges.
"""

import pytest
import time
import wintouch


# Skip all tests in this module if touch API is not available
pytestmark = [
    pytest.mark.skipif(
        not wintouch.is_available(),
        reason="Touch injection API not available (requires Windows 8+)"
    ),
    pytest.mark.requires_touch_injection
]


@pytest.fixture(autouse=True)
def init_touch():
    """Initialize touch injection before each test."""
    wintouch.initialize(max_contacts=10)


class TestSingleTouchSequences:
    """Integration tests for single touch sequences."""

    def test_single_tap(self):
        """Single tap: down then up at same position."""
        # Touch down
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN
        }]) is True
        
        # Touch up
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_UP
        }]) is True

    def test_single_tap_with_delay(self):
        """Single tap with realistic timing."""
        # Touch down
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN
        }]) is True
        
        time.sleep(0.05)  # Brief hold
        
        # Touch up
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_UP
        }]) is True

    def test_single_drag(self):
        """Single finger drag: down, multiple updates, up."""
        # Touch down
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN
        }]) is True
        
        # Drag through multiple points
        for i in range(1, 11):
            assert wintouch.inject([{
                "x": 500 + i * 10,
                "y": 300 + i * 5,
                "flags": wintouch.FLAGS_UPDATE
            }]) is True
        
        # Touch up at final position
        assert wintouch.inject([{
            "x": 600, "y": 350, "flags": wintouch.FLAGS_UP
        }]) is True

    def test_single_drag_with_pressure(self):
        """Single finger drag with varying pressure."""
        # Touch down with standard pressure (Microsoft sample uses 32000)
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN,
            "pressure": 16000
        }]) is True

        # Increase pressure while dragging (use values in Microsoft's range)
        last_y = 300
        for i, pressure in enumerate([20000, 24000, 28000, 32000]):
            last_y = 300 + i * 10
            assert wintouch.inject([{
                "x": 500, "y": last_y,
                "flags": wintouch.FLAGS_UPDATE,
                "pressure": pressure
            }]) is True

        # Touch up at last position (must match previous UPDATE position)
        assert wintouch.inject([{
            "x": 500, "y": last_y, "flags": wintouch.FLAGS_UP
        }]) is True

    def test_long_press(self):
        """Long press: down, hold, up."""
        # Touch down
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_DOWN
        }]) is True
        
        # Hold for 500ms (simulated)
        time.sleep(0.5)
        
        # Touch up
        assert wintouch.inject([{
            "x": 500, "y": 300, "flags": wintouch.FLAGS_UP
        }]) is True


class TestMultiTouchSequences:
    """Integration tests for multi-touch sequences."""

    def test_two_finger_tap(self):
        """Two finger tap: both down, both up."""
        wintouch.initialize(max_contacts=2)
        
        # Both fingers down
        assert wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Both fingers up
        assert wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_pinch_in(self):
        """Pinch-in gesture: two fingers moving closer together."""
        wintouch.initialize(max_contacts=2)
        
        # Start with fingers apart
        assert wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Move fingers closer together
        for i in range(1, 6):
            offset = 100 - i * 20  # 80, 60, 40, 20, 0
            assert wintouch.inject([
                {"x": 500 - offset, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
                {"x": 500 + offset, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
            ]) is True
        
        # Release both fingers
        assert wintouch.inject([
            {"x": 500, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 500, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_pinch_out(self):
        """Pinch-out (zoom) gesture: two fingers moving apart."""
        wintouch.initialize(max_contacts=2)
        
        # Start with fingers close together
        assert wintouch.inject([
            {"x": 480, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 520, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Move fingers apart
        for i in range(1, 6):
            offset = 20 + i * 20  # 40, 60, 80, 100, 120
            assert wintouch.inject([
                {"x": 500 - offset, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
                {"x": 500 + offset, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
            ]) is True
        
        # Release both fingers
        assert wintouch.inject([
            {"x": 380, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 620, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_two_finger_scroll(self):
        """Two finger scroll: both fingers moving in same direction."""
        wintouch.initialize(max_contacts=2)
        
        # Start with fingers side by side
        assert wintouch.inject([
            {"x": 450, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 550, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Scroll down
        for i in range(1, 6):
            y = 300 + i * 20
            assert wintouch.inject([
                {"x": 450, "y": y, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
                {"x": 550, "y": y, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
            ]) is True
        
        # Release both fingers
        assert wintouch.inject([
            {"x": 450, "y": 400, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 550, "y": 400, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_rotate_gesture(self):
        """Rotate gesture: two fingers rotating around center."""
        import math
        wintouch.initialize(max_contacts=2)
        
        center_x, center_y = 500, 300
        radius = 80
        
        # Start horizontal
        assert wintouch.inject([
            {"x": center_x - radius, "y": center_y, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": center_x + radius, "y": center_y, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Rotate 90 degrees
        for angle_deg in range(15, 91, 15):
            angle_rad = math.radians(angle_deg)
            x0 = int(center_x - radius * math.cos(angle_rad))
            y0 = int(center_y - radius * math.sin(angle_rad))
            x1 = int(center_x + radius * math.cos(angle_rad))
            y1 = int(center_y + radius * math.sin(angle_rad))
            assert wintouch.inject([
                {"x": x0, "y": y0, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
                {"x": x1, "y": y1, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
            ]) is True
        
        # Release at vertical position
        assert wintouch.inject([
            {"x": center_x, "y": center_y - radius, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": center_x, "y": center_y + radius, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True


class TestComplexSequences:
    """Integration tests for complex touch sequences."""

    def test_sequential_taps(self):
        """Multiple taps in sequence."""
        for i in range(5):
            x = 300 + i * 100
            
            # Tap
            assert wintouch.inject([{
                "x": x, "y": 300, "flags": wintouch.FLAGS_DOWN
            }]) is True
            
            assert wintouch.inject([{
                "x": x, "y": 300, "flags": wintouch.FLAGS_UP
            }]) is True

    def test_staggered_multi_touch(self):
        """Staggered touch: first finger down, second finger down, both up."""
        wintouch.initialize(max_contacts=2)
        
        # First finger down
        assert wintouch.inject([{
            "x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN
        }]) is True
        
        # Second finger down (first still held)
        assert wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Both fingers up
        assert wintouch.inject([
            {"x": 400, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 600, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_three_finger_gesture(self):
        """Three finger touch sequence."""
        wintouch.initialize(max_contacts=3)
        
        # All three fingers down
        assert wintouch.inject([
            {"x": 350, "y": 300, "pointer_id": 0, "flags": wintouch.FLAGS_DOWN},
            {"x": 500, "y": 300, "pointer_id": 1, "flags": wintouch.FLAGS_DOWN},
            {"x": 650, "y": 300, "pointer_id": 2, "flags": wintouch.FLAGS_DOWN},
        ]) is True
        
        # Swipe down with all three
        for y in range(320, 401, 20):
            assert wintouch.inject([
                {"x": 350, "y": y, "pointer_id": 0, "flags": wintouch.FLAGS_UPDATE},
                {"x": 500, "y": y, "pointer_id": 1, "flags": wintouch.FLAGS_UPDATE},
                {"x": 650, "y": y, "pointer_id": 2, "flags": wintouch.FLAGS_UPDATE},
            ]) is True
        
        # All three fingers up
        assert wintouch.inject([
            {"x": 350, "y": 400, "pointer_id": 0, "flags": wintouch.FLAGS_UP},
            {"x": 500, "y": 400, "pointer_id": 1, "flags": wintouch.FLAGS_UP},
            {"x": 650, "y": 400, "pointer_id": 2, "flags": wintouch.FLAGS_UP},
        ]) is True

    def test_max_contacts(self):
        """Test with maximum number of contacts (10)."""
        wintouch.initialize(max_contacts=10)
        
        # All 10 fingers down
        contacts_down = [
            {"x": 100 + i * 80, "y": 300, "pointer_id": i, "flags": wintouch.FLAGS_DOWN}
            for i in range(10)
        ]
        assert wintouch.inject(contacts_down) is True
        
        # All 10 fingers up
        contacts_up = [
            {"x": 100 + i * 80, "y": 300, "pointer_id": i, "flags": wintouch.FLAGS_UP}
            for i in range(10)
        ]
        assert wintouch.inject(contacts_up) is True
