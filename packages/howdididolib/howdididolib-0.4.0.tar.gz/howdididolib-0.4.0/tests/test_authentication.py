"""Tests for authentication module."""
import pytest
import aiohttp
from unittest.mock import Mock, patch, MagicMock
from yarl import URL
from howdididolib.authentication import AuthenticationClient
from howdididolib.exceptions import InvalidAuth
from howdididolib.const import AUTH_COOKIE_NAME


class TestAuthenticationClient:
    def test_init(self):
        """Test AuthenticationClient initialization."""
        session = Mock(spec=aiohttp.ClientSession)
        client = AuthenticationClient(session, "user", "pass", "custom_cookie.dat")

        assert client.session == session
        assert client.username == "user"
        assert client.password == "pass"
        assert client.auth_cookie_filename == "custom_cookie.dat"

    def test_init_defaults(self):
        """Test AuthenticationClient initialization with defaults."""
        session = Mock(spec=aiohttp.ClientSession)
        client = AuthenticationClient(session)

        assert client.session == session
        assert client.username is None
        assert client.password is None
        assert client.auth_cookie_filename == "howdidido_auth_cookie.dat"

    @pytest.mark.asyncio
    async def test_login_success(self, aio_mock):
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

        aio_mock.get("https://www.howdidido.com/Account/Login", status=200, body=login_html)
        aio_mock.post("https://www.howdidido.com/Account/Login", status=200)

        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            # Mock the cookie being set
            from yarl import URL
            session.cookie_jar.update_cookies({AUTH_COOKIE_NAME: "mock_cookie_val"}, URL("https://www.howdidido.com"))
            await client.login()
            # Check that the cookie is still there
            cookies = session.cookie_jar.filter_cookies(URL("https://www.howdidido.com"))
            assert AUTH_COOKIE_NAME in cookies

    @pytest.mark.asyncio
    async def test_login_no_credentials(self, aio_mock):
        """Test login with no credentials provided."""
        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session)  # No username/password

            login_html = '<div id="login-control"><form action="/Account/Login"><input name="test" value="1"></form></div>'
            aio_mock.get("https://www.howdidido.com/Account/Login", status=200, body=login_html)
            aio_mock.post("https://www.howdidido.com/Account/Login", status=200)

            with pytest.raises(InvalidAuth):
                await client.login()

    @pytest.mark.asyncio
    async def test_login_auth_failure(self, aio_mock):
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

    @pytest.mark.asyncio
    async def test_login_auth_failure(self, aio_mock):
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

        aio_mock.get("https://www.howdidido.com/Account/Login", status=200, body=login_html)
        aio_mock.post("https://www.howdidido.com/Account/Login", status=200)

        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session, "testuser", "testpass")
            with pytest.raises(InvalidAuth, match="Authentication failed"):
                await client.login()

    @pytest.mark.asyncio
    async def test_login_persistent(self, aio_mock):
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

        aio_mock.get("https://www.howdidido.com/Account/Login", status=200, body=login_html)
        aio_mock.post("https://www.howdidido.com/Account/Login", status=200)

        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session, "testuser", "testpass")

            # Mock the cookie jar to return the auth cookie
            from unittest.mock import MagicMock
            mock_cookie = MagicMock()
            mock_cookie.value = "mock_auth_cookie"
            session.cookie_jar.filter_cookies = MagicMock(return_value={AUTH_COOKIE_NAME: mock_cookie})

            await client.login(persistent=True)

            # Check that the cookie was set
            cookies = session.cookie_jar.filter_cookies(URL("https://www.howdidido.com"))
            assert AUTH_COOKIE_NAME in cookies

    @pytest.mark.asyncio
    async def test_login_not_persistent(self, aio_mock):
        """Test login with persistent=False."""
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

        aio_mock.get("https://www.howdidido.com/Account/Login", status=200, body=login_html)
        aio_mock.post("https://www.howdidido.com/Account/Login", status=200)

        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session, "testuser", "testpass")

            # Mock the cookie jar to return the auth cookie
            from unittest.mock import MagicMock
            mock_cookie = MagicMock()
            mock_cookie.value = "mock_auth_cookie"
            session.cookie_jar.filter_cookies = MagicMock(return_value={AUTH_COOKIE_NAME: mock_cookie})

            await client.login(persistent=False)

            # Check that the cookie was set
            cookies = session.cookie_jar.filter_cookies(URL("https://www.howdidido.com"))
            assert AUTH_COOKIE_NAME in cookies

    @pytest.mark.asyncio
    async def test_save_auth_cookie(self):
        """Test saving auth cookie."""
        async with aiohttp.ClientSession() as session:
            # Simulate setting a cookie
            from yarl import URL
            session.cookie_jar.update_cookies({AUTH_COOKIE_NAME: "auth_val"}, URL("https://www.howdidido.com"))
            session.cookie_jar.update_cookies({"other_cookie": "other_val"}, URL("https://www.howdidido.com"))
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
        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session, auth_cookie_filename="test_cookies.json")

            cookie_data = {AUTH_COOKIE_NAME: "restored_val"}

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=cookie_data):
                    result = await client.restore_auth_cookie()

            assert result is True
            # Check that the cookie was restored
            cookies = session.cookie_jar.filter_cookies(URL("https://www.howdidido.com"))
            assert AUTH_COOKIE_NAME in cookies
            assert cookies[AUTH_COOKIE_NAME].value == "restored_val"

    @pytest.mark.asyncio
    async def test_restore_auth_cookie_file_not_found(self):
        """Test cookie restoration when file doesn't exist."""
        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session)

            with patch("builtins.open", side_effect=FileNotFoundError):
                with pytest.raises(InvalidAuth, match="Authentication cookie file not found"):
                    await client.restore_auth_cookie()

    @pytest.mark.asyncio
    async def test_restore_auth_cookie_no_auth_cookie(self):
        """Test cookie restoration when no auth cookie in jar."""
        async with aiohttp.ClientSession() as session:
            client = AuthenticationClient(session)

            cookie_data = {"other_cookie": "val"}

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=cookie_data):
                    with pytest.raises(InvalidAuth, match="Authentication cookie not found"):
                        await client.restore_auth_cookie()
