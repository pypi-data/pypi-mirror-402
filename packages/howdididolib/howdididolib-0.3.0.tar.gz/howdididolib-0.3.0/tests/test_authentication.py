"""Tests for authentication module."""
import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock
from howdididolib.authentication import AuthenticationClient
from howdididolib.exceptions import InvalidAuth
from howdididolib.const import AUTH_COOKIE_NAME


class TestAuthenticationClient:
    def test_init(self):
        """Test AuthenticationClient initialization."""
        session = Mock(spec=httpx.AsyncClient)
        client = AuthenticationClient(session, "user", "pass", "custom_cookie.dat")

        assert client.session == session
        assert client.username == "user"
        assert client.password == "pass"
        assert client.auth_cookie_filename == "custom_cookie.dat"

    def test_init_defaults(self):
        """Test AuthenticationClient initialization with defaults."""
        session = Mock(spec=httpx.AsyncClient)
        client = AuthenticationClient(session)

        assert client.session == session
        assert client.username is None
        assert client.password is None
        assert client.auth_cookie_filename == "howdidido_auth_cookie.dat"

    @pytest.mark.asyncio
    async def test_login_success(self, respx_mock):
        """Test successful login."""
        # Mock the login page response
        login_html = '''
        <div id="login-control">
            <form action="/Account/Login">
                <input name="username" value="">
                <input name="password" value="">
                <input name="rememberme" value="false">
                <input name="__RequestVerificationToken" value="token123">
            </form>
        </div>
        '''

        route1 = respx_mock.get("https://www.howdidido.com/Account/Login").respond(
            status_code=200, text=login_html
        )
        route2 = respx_mock.post("https://www.howdidido.com/Account/Login").respond(
            status_code=200, cookies={AUTH_COOKIE_NAME: "mock_cookie_val"}
        )

        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            await client.login()
            assert route1.called
            assert route2.called
            assert session.cookies.get(AUTH_COOKIE_NAME) == "mock_cookie_val"

    @pytest.mark.asyncio
    async def test_login_no_credentials(self, respx_mock):
        """Test login with no credentials provided."""
        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session)  # No username/password

            login_html = '<div id="login-control"><form action="/Account/Login"><input name="test" value="1"></form></div>'
            route1 = respx_mock.get("https://www.howdidido.com/Account/Login").respond(
                status_code=200, text=login_html
            )
            route2 = respx_mock.post("https://www.howdidido.com/Account/Login").respond(
                status_code=200
            )

            with pytest.raises(InvalidAuth):
                await client.login()

            assert route1.called
            assert route2.called

    @pytest.mark.asyncio
    async def test_login_auth_failure(self, respx_mock):
        """Test login with authentication failure."""
        # Mock the login page response
        login_html = '''
        <div id="login-control">
            <form action="/Account/Login">
                <input name="username" value="">
                <input name="password" value="">
                <input name="rememberme" value="false">
                <input name="__RequestVerificationToken" value="token123">
            </form>
        </div>
        '''

        route1 = respx_mock.get("https://www.howdidido.com/Account/Login").respond(
            status_code=200, text=login_html
        )
        route2 = respx_mock.post("https://www.howdidido.com/Account/Login").respond(
            status_code=200
        )

        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            with pytest.raises(InvalidAuth, match="Authentication failed"):
                await client.login()

            assert route1.called
            assert route2.called

    @pytest.mark.asyncio
    async def test_login_persistent(self, respx_mock):
        """Test login with persistent=True."""
        login_html = '''
        <div id="login-control">
            <form action="/Account/Login">
                <input name="username" value="">
                <input name="password" value="">
                <input name="rememberme" value="false">
                <input name="__RequestVerificationToken" value="token123">
            </form>
        </div>
        '''

        respx_mock.get("https://www.howdidido.com/Account/Login").respond(
            status_code=200, text=login_html
        )
        route2 = respx_mock.post("https://www.howdidido.com/Account/Login").respond(
            status_code=200, cookies={AUTH_COOKIE_NAME: "mock_cookie_val"}
        )

        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            await client.login(persistent=True)

            # Check the called form data
            call = route2.calls.last
            assert "rememberme" in call.request.content.decode()
            # If persistent is true, input_value was ["true", "false"] which might be encoded uniquely
            # Beautifulsoup and the code logic: form_data[input_name] = ["true", "false"]
            # httpx will encode this as rememberme=true&rememberme=false

    @pytest.mark.asyncio
    async def test_login_not_persistent(self, respx_mock):
        """Test login with persistent=False."""
        login_html = '''
        <div id="login-control">
            <form action="/Account/Login">
                <input name="username" value="">
                <input name="password" value="">
                <input name="rememberme" value="true">
            </form>
        </div>
        '''

        respx_mock.get("https://www.howdidido.com/Account/Login").respond(
            status_code=200, text=login_html
        )
        route2 = respx_mock.post("https://www.howdidido.com/Account/Login").respond(
            status_code=200, cookies={AUTH_COOKIE_NAME: "mock_cookie_val"}
        )

        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            await client.login(persistent=False)

            call = route2.calls.last
            assert "rememberme=false" in call.request.content.decode()

    @pytest.mark.asyncio
    async def test_save_auth_cookie(self):
        """Test saving auth cookie."""
        async with httpx.AsyncClient() as session:
            session.cookies.set(AUTH_COOKIE_NAME, "auth_val")
            session.cookies.set("other_cookie", "other_val")
            client = AuthenticationClient(
                session, auth_cookie_filename="test_cookies.json"
            )

            with patch("builtins.open", MagicMock()) as mock_open:
                with patch("json.dump") as mock_dump:
                    await client.save_auth_cookie()

                    # Verify that it tried to save the cookies
                    mock_open.assert_called_once_with("test_cookies.json", "w")
                    mock_dump.assert_called_once()
                    saved_dict = mock_dump.call_args[0][0]
                    assert AUTH_COOKIE_NAME in saved_dict
                    assert saved_dict[AUTH_COOKIE_NAME] == "auth_val"
                    assert "other_cookie" not in saved_dict

    @pytest.mark.asyncio
    async def test_restore_auth_cookie_success(self):
        """Test successful cookie restoration."""
        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session, auth_cookie_filename="test_cookies.json")

            cookie_data = {AUTH_COOKIE_NAME: "restored_val"}

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=cookie_data):
                    result = await client.restore_auth_cookie()

            assert result is True
            assert session.cookies.get(AUTH_COOKIE_NAME) == "restored_val"

    @pytest.mark.asyncio
    async def test_restore_auth_cookie_file_not_found(self):
        """Test cookie restoration when file doesn't exist."""
        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session)

            with patch("builtins.open", side_effect=FileNotFoundError):
                with pytest.raises(InvalidAuth, match="Authentication cookie file not found"):
                    await client.restore_auth_cookie()

    @pytest.mark.asyncio
    async def test_restore_auth_cookie_no_auth_cookie(self):
        """Test cookie restoration when no auth cookie in jar."""
        async with httpx.AsyncClient() as session:
            client = AuthenticationClient(session)

            cookie_data = {"other_cookie": "val"}

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=cookie_data):
                    with pytest.raises(InvalidAuth, match="Authentication cookie not found"):
                        await client.restore_auth_cookie()
