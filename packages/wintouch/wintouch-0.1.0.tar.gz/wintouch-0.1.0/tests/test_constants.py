"""
Tests for wintouch constants.

These tests verify:
- All expected constants are exported
- Constants have correct values
- Flag combinations are valid
"""

import wintouch


class TestPointerFlags:
    """Tests for pointer flag constants."""

    def test_pointer_flag_none_value(self):
        """POINTER_FLAG_NONE should be 0."""
        assert wintouch.POINTER_FLAG_NONE == 0x00000000

    def test_pointer_flag_new_value(self):
        """POINTER_FLAG_NEW should be 0x00000001."""
        assert wintouch.POINTER_FLAG_NEW == 0x00000001

    def test_pointer_flag_inrange_value(self):
        """POINTER_FLAG_INRANGE should be 0x00000002."""
        assert wintouch.POINTER_FLAG_INRANGE == 0x00000002

    def test_pointer_flag_incontact_value(self):
        """POINTER_FLAG_INCONTACT should be 0x00000004."""
        assert wintouch.POINTER_FLAG_INCONTACT == 0x00000004

    def test_pointer_flag_firstbutton_value(self):
        """POINTER_FLAG_FIRSTBUTTON should be 0x00000010."""
        assert wintouch.POINTER_FLAG_FIRSTBUTTON == 0x00000010

    def test_pointer_flag_primary_value(self):
        """POINTER_FLAG_PRIMARY should be 0x00002000."""
        assert wintouch.POINTER_FLAG_PRIMARY == 0x00002000

    def test_pointer_flag_confidence_value(self):
        """POINTER_FLAG_CONFIDENCE should be 0x00004000."""
        assert wintouch.POINTER_FLAG_CONFIDENCE == 0x00004000

    def test_pointer_flag_canceled_value(self):
        """POINTER_FLAG_CANCELED should be 0x00008000."""
        assert wintouch.POINTER_FLAG_CANCELED == 0x00008000

    def test_pointer_flag_down_value(self):
        """POINTER_FLAG_DOWN should be 0x00010000."""
        assert wintouch.POINTER_FLAG_DOWN == 0x00010000

    def test_pointer_flag_update_value(self):
        """POINTER_FLAG_UPDATE should be 0x00020000."""
        assert wintouch.POINTER_FLAG_UPDATE == 0x00020000

    def test_pointer_flag_up_value(self):
        """POINTER_FLAG_UP should be 0x00040000."""
        assert wintouch.POINTER_FLAG_UP == 0x00040000


class TestTouchFlags:
    """Tests for touch flag constants."""

    def test_touch_flag_none_value(self):
        """TOUCH_FLAG_NONE should be 0."""
        assert wintouch.TOUCH_FLAG_NONE == 0x00000000


class TestTouchMasks:
    """Tests for touch mask constants."""

    def test_touch_mask_none_value(self):
        """TOUCH_MASK_NONE should be 0."""
        assert wintouch.TOUCH_MASK_NONE == 0x00000000

    def test_touch_mask_contactarea_value(self):
        """TOUCH_MASK_CONTACTAREA should be 0x00000001."""
        assert wintouch.TOUCH_MASK_CONTACTAREA == 0x00000001

    def test_touch_mask_orientation_value(self):
        """TOUCH_MASK_ORIENTATION should be 0x00000002."""
        assert wintouch.TOUCH_MASK_ORIENTATION == 0x00000002

    def test_touch_mask_pressure_value(self):
        """TOUCH_MASK_PRESSURE should be 0x00000004."""
        assert wintouch.TOUCH_MASK_PRESSURE == 0x00000004


class TestFeedbackModes:
    """Tests for feedback mode constants."""

    def test_feedback_default_value(self):
        """FEEDBACK_DEFAULT should be 0x1."""
        assert wintouch.FEEDBACK_DEFAULT == 0x1

    def test_feedback_indirect_value(self):
        """FEEDBACK_INDIRECT should be 0x2."""
        assert wintouch.FEEDBACK_INDIRECT == 0x2

    def test_feedback_none_value(self):
        """FEEDBACK_NONE should be 0x3."""
        assert wintouch.FEEDBACK_NONE == 0x3


class TestConvenienceFlags:
    """Tests for convenience flag combinations."""

    def test_flags_down_includes_down(self):
        """FLAGS_DOWN should include POINTER_FLAG_DOWN."""
        assert wintouch.FLAGS_DOWN & wintouch.POINTER_FLAG_DOWN

    def test_flags_down_includes_inrange(self):
        """FLAGS_DOWN should include POINTER_FLAG_INRANGE."""
        assert wintouch.FLAGS_DOWN & wintouch.POINTER_FLAG_INRANGE

    def test_flags_down_includes_incontact(self):
        """FLAGS_DOWN should include POINTER_FLAG_INCONTACT."""
        assert wintouch.FLAGS_DOWN & wintouch.POINTER_FLAG_INCONTACT

    def test_flags_down_minimal(self):
        """FLAGS_DOWN uses minimal flags per Microsoft sample.

        Microsoft's official sample uses only DOWN | INRANGE | INCONTACT.
        PRIMARY and CONFIDENCE are NOT required and can cause ERROR_INVALID_PARAMETER.
        """
        expected = (wintouch.POINTER_FLAG_DOWN |
                   wintouch.POINTER_FLAG_INRANGE |
                   wintouch.POINTER_FLAG_INCONTACT)
        assert wintouch.FLAGS_DOWN == expected

    def test_flags_update_includes_update(self):
        """FLAGS_UPDATE should include POINTER_FLAG_UPDATE."""
        assert wintouch.FLAGS_UPDATE & wintouch.POINTER_FLAG_UPDATE

    def test_flags_update_includes_inrange(self):
        """FLAGS_UPDATE should include POINTER_FLAG_INRANGE."""
        assert wintouch.FLAGS_UPDATE & wintouch.POINTER_FLAG_INRANGE

    def test_flags_update_includes_incontact(self):
        """FLAGS_UPDATE should include POINTER_FLAG_INCONTACT."""
        assert wintouch.FLAGS_UPDATE & wintouch.POINTER_FLAG_INCONTACT

    def test_flags_up_minimal(self):
        """FLAGS_UP uses minimal flags per Microsoft sample.

        Microsoft's official sample uses only POINTER_FLAG_UP.
        No other flags are required for touch release.
        """
        assert wintouch.FLAGS_UP == wintouch.POINTER_FLAG_UP


class TestAllExports:
    """Tests to verify all expected symbols are exported."""

    def test_exports_functions(self):
        """All expected functions should be exported."""
        assert hasattr(wintouch, 'initialize')
        assert hasattr(wintouch, 'inject')
        assert hasattr(wintouch, 'is_available')
        assert hasattr(wintouch, 'is_initialized')
        assert hasattr(wintouch, 'get_max_contacts')
        assert hasattr(wintouch, 'diagnose')

    def test_exports_convenience_flags(self):
        """All convenience flags should be exported."""
        assert hasattr(wintouch, 'FLAGS_DOWN')
        assert hasattr(wintouch, 'FLAGS_UPDATE')
        assert hasattr(wintouch, 'FLAGS_UP')

    def test_exports_pointer_flags(self):
        """All pointer flags should be exported."""
        assert hasattr(wintouch, 'POINTER_FLAG_NONE')
        assert hasattr(wintouch, 'POINTER_FLAG_NEW')
        assert hasattr(wintouch, 'POINTER_FLAG_INRANGE')
        assert hasattr(wintouch, 'POINTER_FLAG_INCONTACT')
        assert hasattr(wintouch, 'POINTER_FLAG_FIRSTBUTTON')
        assert hasattr(wintouch, 'POINTER_FLAG_PRIMARY')
        assert hasattr(wintouch, 'POINTER_FLAG_CONFIDENCE')
        assert hasattr(wintouch, 'POINTER_FLAG_CANCELED')
        assert hasattr(wintouch, 'POINTER_FLAG_DOWN')
        assert hasattr(wintouch, 'POINTER_FLAG_UPDATE')
        assert hasattr(wintouch, 'POINTER_FLAG_UP')

    def test_exports_touch_masks(self):
        """All touch masks should be exported."""
        assert hasattr(wintouch, 'TOUCH_FLAG_NONE')
        assert hasattr(wintouch, 'TOUCH_MASK_NONE')
        assert hasattr(wintouch, 'TOUCH_MASK_CONTACTAREA')
        assert hasattr(wintouch, 'TOUCH_MASK_ORIENTATION')
        assert hasattr(wintouch, 'TOUCH_MASK_PRESSURE')

    def test_exports_feedback_modes(self):
        """All feedback modes should be exported."""
        assert hasattr(wintouch, 'FEEDBACK_DEFAULT')
        assert hasattr(wintouch, 'FEEDBACK_INDIRECT')
        assert hasattr(wintouch, 'FEEDBACK_NONE')

    def test_all_list_completeness(self):
        """__all__ should include all public symbols."""
        expected_exports = [
            'initialize', 'inject', 'is_available', 'is_initialized', 'get_max_contacts', 'diagnose',
            'FLAGS_DOWN', 'FLAGS_UPDATE', 'FLAGS_UP',
            'POINTER_FLAG_NONE', 'POINTER_FLAG_NEW', 'POINTER_FLAG_INRANGE',
            'POINTER_FLAG_INCONTACT', 'POINTER_FLAG_FIRSTBUTTON', 'POINTER_FLAG_PRIMARY',
            'POINTER_FLAG_CONFIDENCE', 'POINTER_FLAG_CANCELED', 'POINTER_FLAG_DOWN',
            'POINTER_FLAG_UPDATE', 'POINTER_FLAG_UP',
            'TOUCH_FLAG_NONE', 'TOUCH_MASK_NONE', 'TOUCH_MASK_CONTACTAREA',
            'TOUCH_MASK_ORIENTATION', 'TOUCH_MASK_PRESSURE',
            'FEEDBACK_DEFAULT', 'FEEDBACK_INDIRECT', 'FEEDBACK_NONE',
        ]
        for name in expected_exports:
            assert name in wintouch.__all__, f"{name} not in __all__"
