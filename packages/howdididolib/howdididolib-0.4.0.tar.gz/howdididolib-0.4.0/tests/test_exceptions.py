"""Tests for exceptions module."""
from howdididolib.exceptions import InvalidAuth


class TestInvalidAuth:
    def test_creation(self):
        """Test InvalidAuth exception creation."""
        exception = InvalidAuth("Test message")
        assert str(exception) == "Test message"
        assert isinstance(exception, Exception)

    def test_creation_without_message(self):
        """Test InvalidAuth exception creation without message."""
        exception = InvalidAuth()
        assert str(exception) == ""
        assert isinstance(exception, Exception)
