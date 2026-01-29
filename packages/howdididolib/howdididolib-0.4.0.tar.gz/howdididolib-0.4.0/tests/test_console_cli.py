"""CLI tests for console module."""
from typer.testing import CliRunner
from howdididolib.console import app, sync_main
from howdididolib.const import AUTH_COOKIE_NAME
from unittest.mock import patch, MagicMock, AsyncMock

runner = CliRunner()

def test_sync_main():
    """Test the sync_main entry point."""
    with patch("howdididolib.console.app") as mock_app:
        sync_main()
        mock_app.assert_called_once()

def test_cli_auth_success():
    """Test successful authentication via CLI."""
    with patch("howdididolib.console.AuthenticationClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.login = AsyncMock()
        mock_instance.save_auth_cookie = AsyncMock()

        result = runner.invoke(app, ["auth"], input="testuser\ntestpass\n")
        assert result.exit_code == 0
        assert "Authentication successful!" in result.stdout

def test_cli_auth_failure():
    """Test authentication failure via CLI."""
    import aiohttp
    with patch("howdididolib.console.AuthenticationClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.login = AsyncMock(side_effect=aiohttp.ClientError("Login failed"))

        result = runner.invoke(app, ["auth", "--username", "testuser", "--password", "testpass"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.stdout

def test_cli_bookings_no_auth():
    """Test bookings command when not authenticated."""
    from howdididolib.exceptions import InvalidAuth
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", side_effect=InvalidAuth):
        result = runner.invoke(app, ["bookings"])
        assert result.exit_code == 1
        assert "No saved credentials found" in result.stdout

def test_cli_bookings_success():
    """Test successful bookings fetch via CLI."""
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        mock_data = MagicMock()
        mock_data.booked_events = []
        mock_data.bookable_events = []
        with patch("howdididolib.bookings.BookingClient.get", return_value=mock_data):
            result = runner.invoke(app, ["bookings"])
            assert result.exit_code == 0
            assert "No bookings found" in result.stdout

def test_cli_fixtures_success():
    """Test successful fixtures fetch via CLI."""
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        with patch("howdididolib.fixtures.FixtureClient.get", return_value=[]):
            result = runner.invoke(app, ["fixtures"])
            assert result.exit_code == 0
            assert "No fixtures found" in result.stdout
