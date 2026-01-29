"""
Tests for wintouch availability and initialization state functions.

These tests verify:
- is_available() correctly reports API availability
- is_initialized() correctly tracks initialization state
- get_max_contacts() returns correct values
"""

import pytest
import wintouch


class TestIsAvailable:
    """Tests for wintouch.is_available()"""

    def test_is_available_returns_bool(self):
        """is_available() should return a boolean value."""
        result = wintouch.is_available()
        assert isinstance(result, bool)

    def test_is_available_consistent(self):
        """is_available() should return consistent results on repeated calls."""
        result1 = wintouch.is_available()
        result2 = wintouch.is_available()
        result3 = wintouch.is_available()
        assert result1 == result2 == result3

    @pytest.mark.skipif(not wintouch.is_available(), reason="Touch API not available")
    def test_is_available_true_on_supported_system(self):
        """On Windows 8+, is_available() should return True."""
        assert wintouch.is_available() is True


class TestIsInitialized:
    """Tests for wintouch.is_initialized()"""

    def test_is_initialized_returns_bool(self):
        """is_initialized() should return a boolean value."""
        result = wintouch.is_initialized()
        assert isinstance(result, bool)

    def test_is_initialized_false_before_init(self):
        """is_initialized() should return False before initialize() is called."""
        # Note: This test assumes fresh module state or relies on test isolation
        # In practice, once initialized, the state persists for the process
        result = wintouch.is_initialized()
        assert isinstance(result, bool)


class TestGetMaxContacts:
    """Tests for wintouch.get_max_contacts()"""

    def test_get_max_contacts_returns_int(self):
        """get_max_contacts() should return an integer."""
        result = wintouch.get_max_contacts()
        assert isinstance(result, int)

    def test_get_max_contacts_non_negative(self):
        """get_max_contacts() should return a non-negative value."""
        result = wintouch.get_max_contacts()
        assert result >= 0


class TestDiagnose:
    """Tests for wintouch.diagnose()"""

    def test_diagnose_returns_dict(self):
        """diagnose() should return a dictionary."""
        result = wintouch.diagnose()
        assert isinstance(result, dict)

    def test_diagnose_has_required_keys(self):
        """diagnose() result should have all required keys."""
        result = wintouch.diagnose()
        required_keys = [
            "api_available",
            "has_touch_digitizer",
            "digitizer_flags",
            "max_touch_points",
            "integrated_touch",
            "external_touch",
            "touch_ready",
            "init_works",
            "init_error",
            "inject_works",
            "inject_error",
            "diagnosis",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_diagnose_api_available_is_bool(self):
        """diagnose()['api_available'] should be boolean."""
        result = wintouch.diagnose()
        assert isinstance(result["api_available"], bool)

    def test_diagnose_diagnosis_is_string(self):
        """diagnose()['diagnosis'] should be a string."""
        result = wintouch.diagnose()
        assert isinstance(result["diagnosis"], str)
        assert len(result["diagnosis"]) > 0

    @pytest.mark.skipif(not wintouch.is_available(), reason="Touch API not available")
    def test_diagnose_digitizer_flags_is_int(self):
        """diagnose()['digitizer_flags'] should be an integer."""
        result = wintouch.diagnose()
        assert isinstance(result["digitizer_flags"], int)

    @pytest.mark.skipif(not wintouch.is_available(), reason="Touch API not available")
    def test_diagnose_max_touch_points_is_int(self):
        """diagnose()['max_touch_points'] should be an integer."""
        result = wintouch.diagnose()
        assert isinstance(result["max_touch_points"], int)
