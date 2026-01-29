"""
Tests for wintouch.initialize() function.

These tests verify:
- Valid parameter combinations
- Invalid parameter handling
- State changes after initialization
- Error conditions
"""

import pytest
import wintouch


# Skip all tests in this module if touch API is not available
pytestmark = pytest.mark.skipif(
    not wintouch.is_available(),
    reason="Touch injection API not available (requires Windows 8+)"
)


class TestInitializeValidParams:
    """Tests for initialize() with valid parameters."""

    def test_initialize_default_params(self):
        """initialize() with default parameters should succeed."""
        result = wintouch.initialize()
        assert result is True

    def test_initialize_max_contacts_1(self):
        """initialize(max_contacts=1) should succeed."""
        result = wintouch.initialize(max_contacts=1)
        assert result is True

    def test_initialize_max_contacts_2(self):
        """initialize(max_contacts=2) should succeed."""
        result = wintouch.initialize(max_contacts=2)
        assert result is True

    def test_initialize_max_contacts_5(self):
        """initialize(max_contacts=5) should succeed."""
        result = wintouch.initialize(max_contacts=5)
        assert result is True

    def test_initialize_max_contacts_10(self):
        """initialize(max_contacts=10) - maximum allowed - should succeed."""
        result = wintouch.initialize(max_contacts=10)
        assert result is True

    def test_initialize_feedback_default(self):
        """initialize(feedback_mode=FEEDBACK_DEFAULT) should succeed."""
        result = wintouch.initialize(feedback_mode=wintouch.FEEDBACK_DEFAULT)
        assert result is True

    def test_initialize_feedback_indirect(self):
        """initialize(feedback_mode=FEEDBACK_INDIRECT) should succeed."""
        result = wintouch.initialize(feedback_mode=wintouch.FEEDBACK_INDIRECT)
        assert result is True

    def test_initialize_feedback_none(self):
        """initialize(feedback_mode=FEEDBACK_NONE) should succeed."""
        result = wintouch.initialize(feedback_mode=wintouch.FEEDBACK_NONE)
        assert result is True

    def test_initialize_both_params(self):
        """initialize() with both parameters should succeed."""
        result = wintouch.initialize(max_contacts=3, feedback_mode=wintouch.FEEDBACK_NONE)
        assert result is True


class TestInitializeInvalidParams:
    """Tests for initialize() with invalid parameters."""

    def test_initialize_max_contacts_zero(self):
        """initialize(max_contacts=0) should raise ValueError."""
        with pytest.raises(ValueError, match="max_contacts must be between 1 and 10"):
            wintouch.initialize(max_contacts=0)

    def test_initialize_max_contacts_negative(self):
        """initialize(max_contacts=-1) should raise ValueError or OverflowError."""
        with pytest.raises((ValueError, OverflowError)):
            wintouch.initialize(max_contacts=-1)

    def test_initialize_max_contacts_11(self):
        """initialize(max_contacts=11) should raise ValueError."""
        with pytest.raises(ValueError, match="max_contacts must be between 1 and 10"):
            wintouch.initialize(max_contacts=11)

    def test_initialize_max_contacts_100(self):
        """initialize(max_contacts=100) should raise ValueError."""
        with pytest.raises(ValueError, match="max_contacts must be between 1 and 10"):
            wintouch.initialize(max_contacts=100)

    def test_initialize_max_contacts_wrong_type_string(self):
        """initialize(max_contacts='5') should raise TypeError."""
        with pytest.raises(TypeError):
            wintouch.initialize(max_contacts='5')

    def test_initialize_max_contacts_wrong_type_float(self):
        """initialize(max_contacts=5.5) should raise TypeError."""
        with pytest.raises(TypeError):
            wintouch.initialize(max_contacts=5.5)

    def test_initialize_feedback_wrong_type(self):
        """initialize(feedback_mode='default') should raise TypeError."""
        with pytest.raises(TypeError):
            wintouch.initialize(feedback_mode='default')


class TestInitializeState:
    """Tests for state changes after initialize()."""

    def test_is_initialized_true_after_init(self):
        """is_initialized() should return True after successful initialize()."""
        wintouch.initialize()
        assert wintouch.is_initialized() is True

    def test_get_max_contacts_after_init_default(self):
        """get_max_contacts() should return 1 after initialize() with defaults."""
        wintouch.initialize(max_contacts=1)
        assert wintouch.get_max_contacts() == 1

    def test_get_max_contacts_after_init_custom(self):
        """get_max_contacts() should return configured value after initialize()."""
        wintouch.initialize(max_contacts=5)
        assert wintouch.get_max_contacts() == 5

    def test_get_max_contacts_after_init_max(self):
        """get_max_contacts() should return 10 after initialize(max_contacts=10)."""
        wintouch.initialize(max_contacts=10)
        assert wintouch.get_max_contacts() == 10
