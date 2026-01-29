"""CLI tests for console module."""
from typer.testing import CliRunner
import respx
import httpx
from howdididolib.console import app, sync_main
from howdididolib.const import AUTH_COOKIE_NAME
from unittest.mock import patch, MagicMock

runner = CliRunner()

def test_sync_main():
    """Test the sync_main entry point."""
    with patch("howdididolib.console.app") as mock_app:
        sync_main()
        mock_app.assert_called_once()

@respx.mock
def test_cli_auth_success():
    """Test successful authentication via CLI."""
    login_html = '<div id="login-control"><form action="/Account/Login"></form></div>'
    respx.get("https://www.howdidido.com/Account/Login").respond(status_code=200, text=login_html)
    respx.post("https://www.howdidido.com/Account/Login").respond(
        status_code=200, cookies={AUTH_COOKIE_NAME: "mock_cookie"}
    )

    with patch("howdididolib.authentication.AuthenticationClient.save_auth_cookie", return_value=None):
        result = runner.invoke(app, ["auth"], input="testuser\ntestpass\n")
        assert result.exit_code == 0
        assert "Authentication successful!" in result.stdout

@respx.mock
def test_cli_auth_failure():
    """Test authentication failure via CLI."""
    login_html = '<div id="login-control"><form action="/Account/Login"></form></div>'
    respx.get("https://www.howdidido.com/Account/Login").respond(status_code=200, text=login_html)
    respx.post("https://www.howdidido.com/Account/Login").respond(status_code=200) # No cookie = failure

    result = runner.invoke(app, ["auth", "--username", "testuser", "--password", "testpass"])
    assert result.exit_code == 1
    assert "Authentication failed" in result.stdout

@respx.mock
def test_cli_bookings_no_auth():
    """Test bookings command when not authenticated."""
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", side_effect=Exception("No saved credentials")):
        # The code in console.py catches InvalidAuth, but restore_auth_cookie might raise something else or we can mock it to raise InvalidAuth
        from howdididolib.exceptions import InvalidAuth
        with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", side_effect=InvalidAuth):
            result = runner.invoke(app, ["bookings"])
            assert result.exit_code == 1
            assert "No saved credentials found" in result.stdout

@respx.mock
def test_cli_bookings_success():
    """Test successful bookings fetch via CLI."""
    respx.get("https://www.howdidido.com/Booking").respond(status_code=200, text="<html></html>")

    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        mock_data = MagicMock()
        mock_data.booked_events = []
        mock_data.bookable_events = []
        with patch("howdididolib.bookings.BookingClient.get", return_value=mock_data):
            result = runner.invoke(app, ["bookings"])
            assert result.exit_code == 0
            assert "No bookings found" in result.stdout

@respx.mock
def test_cli_fixtures_success():
    """Test successful fixtures fetch via CLI."""
    respx.get("https://www.howdidido.com/Fixture").respond(status_code=200, text="<html></html>")

    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        with patch("howdididolib.fixtures.FixtureClient.get", return_value=[]):
            result = runner.invoke(app, ["fixtures"])
            assert result.exit_code == 0
            assert "No fixtures found" in result.stdout

@respx.mock
def test_cli_bookings_success_with_data():
    """Test successful bookings fetch with data via CLI."""
    from howdididolib.types import BookedEvent, Bookings, BookableEvent
    from datetime import datetime

    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        mock_data = MagicMock(spec=Bookings)
        mock_data.booked_events = [
            BookedEvent(datetime(2026, 1, 20, 10, 0), "Test Booked", ["Player 1"])
        ]
        mock_data.bookable_events = [
            BookableEvent(datetime(2026, 1, 21).date(), "Test Bookable", datetime(2026, 1, 1).date(), datetime(2026, 1, 2).date())
        ]
        with patch("howdididolib.bookings.BookingClient.get", return_value=mock_data):
            result = runner.invoke(app, ["bookings"])
            assert result.exit_code == 0
            assert "Test Booked" in result.stdout
            assert "Test Bookable" in result.stdout

@respx.mock
def test_cli_bookings_http_error():
    """Test bookings command with HTTP error."""
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        with patch("howdididolib.bookings.BookingClient.get", side_effect=httpx.HTTPError("Network error")):
            result = runner.invoke(app, ["bookings"])
            assert result.exit_code == 1
            assert "Failed to fetch bookings" in result.stdout

@respx.mock
def test_cli_fixtures_success_with_data():
    """Test successful fixtures fetch with data via CLI."""
    from howdididolib.types import Fixture
    from datetime import date

    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        mock_fixtures = [
            Fixture(date(2026, 2, 1), "Test Fixture", "Medal", "Description")
        ]
        with patch("howdididolib.fixtures.FixtureClient.get", return_value=mock_fixtures):
            result = runner.invoke(app, ["fixtures"])
            assert result.exit_code == 0
            assert "Test Fixture" in result.stdout

@respx.mock
def test_cli_fixtures_http_error():
    """Test fixtures command with HTTP error."""
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", return_value=None):
        with patch("howdididolib.fixtures.FixtureClient.get", side_effect=httpx.HTTPError("Network error")):
            result = runner.invoke(app, ["fixtures"])
            assert result.exit_code == 1
            assert "Failed to fetch fixtures" in result.stdout

def test_sync_main_unexpected_error():
    """Test sync_main with an unexpected error."""
    with patch("howdididolib.console.app", side_effect=Exception("Unexpected")):
        result = sync_main()
        assert result == 1

@respx.mock
def test_cli_fixtures_no_auth():
    """Test fixtures command when not authenticated."""
    from howdididolib.exceptions import InvalidAuth
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", side_effect=InvalidAuth):
        result = runner.invoke(app, ["fixtures"])
        assert result.exit_code == 1
        assert "No saved credentials found" in result.stdout

def test_sync_main_typer_exit():
    """Test sync_main with a typer.Exit."""
    import typer
    with patch("howdididolib.console.app", side_effect=typer.Exit(code=1)):
        result = sync_main()
        assert result == 1

@respx.mock
def test_cli_auth_debug_logging():
    """Test auth command with debug logging to trigger event hooks."""
    login_html = '<div id="login-control"><form action="/Account/Login"></form></div>'
    respx.get("https://www.howdidido.com/Account/Login").respond(status_code=200, text=login_html)
    respx.post("https://www.howdidido.com/Account/Login").respond(
        status_code=200, cookies={AUTH_COOKIE_NAME: "mock_cookie"}
    )

    with patch("howdididolib.authentication.AuthenticationClient.save_auth_cookie", return_value=None):
        # This will trigger get_session(debug=True) and the hooks during the requests
        result = runner.invoke(app, ["auth", "--debug"], input="testuser\ntestpass\n")
        assert result.exit_code == 0
        assert "Authentication successful!" in result.stdout

def test_cli_debug_logging():
    """Test enabling debug logging via CLI."""
    # This is hard to test output for, but we can verify it doesn't crash
    with patch("howdididolib.authentication.AuthenticationClient.restore_auth_cookie", side_effect=Exception):
        result = runner.invoke(app, ["bookings", "--debug"])
        assert result.exit_code == 1
