"""Tests for mute toggle feature (Phase 8)."""

from xair.utils import parse_bool_value


class TestMuteToggle:
    """Tests for mute toggle functionality."""

    def testparse_bool_value_function_exists(self):
        """parse_bool_value function exists."""
        assert callable(parse_bool_value)

    def testparse_bool_value_toggle(self):
        """parse_bool_value returns 'toggle' for toggle input."""
        result = parse_bool_value("toggle", current=True)
        assert result is False  # Opposite of current

        result = parse_bool_value("toggle", current=False)
        assert result is True  # Opposite of current

    def testparse_bool_value_on(self):
        """parse_bool_value returns True for 'on'."""
        result = parse_bool_value("on", current=False)
        assert result is True

    def testparse_bool_value_off(self):
        """parse_bool_value returns False for 'off'."""
        result = parse_bool_value("off", current=True)
        assert result is False
