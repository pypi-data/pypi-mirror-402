"""Authentication for How Did I Do integration."""

import logging
import json

import aiohttp
import bs4
from yarl import URL

from howdididolib.const import DEFAULT_AUTH_COOKIE_FILE
from howdididolib.const import LOGIN_URL, BASE_URL, AUTH_COOKIE_NAME
from howdididolib.const import USER_AGENT
from howdididolib.exceptions import InvalidAuth

logger = logging.getLogger(__name__)


class AuthenticationClient:
    """Client for handling authentication with the How Did I Do website."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str = None,
        password: str = None,
        auth_cookie_filename: str = DEFAULT_AUTH_COOKIE_FILE,
    ):
        """
        Initialize the authentication client.

        Args:
            session: The aiohttp ClientSession to use for requests.
            username: Optional username for login.
            password: Optional password for login.
            auth_cookie_filename: The filename to use for saving/restoring cookies.
        """
        self.session = session
        self.username = username
        self.password = password
        self.auth_cookie_filename = auth_cookie_filename

    async def login(self, persistent: bool = True):
        """
        Login using username and password via form to obtain authentication cookie.

        Args:
            persistent: Whether to set the 'Remember Me' flag for a long-lived session.

        Raises:
            InvalidAuth: If authentication fails or credentials are incorrect.
            aiohttp.ClientError: If there is a network error.
        """

        async with self.session.get(
            LOGIN_URL,
            headers={
                "user-agent": USER_AGENT,
            },
        ) as resp:
            resp.raise_for_status()
            soup = bs4.BeautifulSoup(await resp.text(), "html.parser")

        # Find the login form within the page
        login_div = soup.find(name="div", id="login-control")
        if not login_div:
            raise InvalidAuth("Could not find login control on the page")

        login_form = login_div.find(name="form")
        if not login_form:
            raise InvalidAuth("Could not find login form on the page")

        login_form_action = login_form.get("action")

        # Create a dictionary to store form data, prepopulating with static hidden fields
        form_data = {}

        # Iterate over input elements within the form to build the POST payload
        for input_element in login_form.find_all('input'):
            input_name = input_element.get('name')
            input_value = input_element.get('value', '')

            if input_name is not None:
                # Fill in user credentials and session preferences
                if input_name.lower() == 'username':
                    input_value = f'{self.username}'
                elif input_name.lower() == 'password':
                    input_value = f'{self.password}'
                elif input_name.lower() == 'rememberme':
                    if persistent:
                        # Some forms send both values when checked
                        input_value = ["true", "false"]
                    else:
                        input_value = "false"

                form_data[input_name] = input_value

        logger.debug("login form data: %s", form_data)

        # Submit the login form
        async with self.session.post(
            f"{BASE_URL}{login_form_action}",
            headers={
                "user-agent": USER_AGENT,
                "Origin": BASE_URL,
                "Referer": f"{BASE_URL}{login_form_action}"
            },
            data=form_data,
        ) as resp:
            resp.raise_for_status()

        # Verify that we received the expected authentication cookie
        auth_cookie = self.session.cookie_jar.filter_cookies(URL(BASE_URL)).get(AUTH_COOKIE_NAME)
        if not auth_cookie:
            raise InvalidAuth("Authentication failed: check username and password")

    async def save_auth_cookie(self):
        """Save session auth cookies to a local JSON file for future sessions."""
        cookies_to_save = {}
        for cookie in self.session.cookie_jar:
            if cookie.key == AUTH_COOKIE_NAME:
                cookies_to_save[cookie.key] = cookie.value
                break
        with open(self.auth_cookie_filename, "w") as f:
            json.dump(cookies_to_save, f)

    async def restore_auth_cookie(self):
        """
        Restore session auth cookies from a local file.

        Returns:
            bool: True if restoration was successful.

        Raises:
            InvalidAuth: If the file is missing, invalid, or doesn't contain the auth cookie.
        """
        try:
            # Load existing cookies from the file
            with open(self.auth_cookie_filename, 'r') as f:
                cookies = json.load(f)

            # Add cookies to the session
            for name, value in cookies.items():
                self.session.cookie_jar.update_cookies({name: value})

            # Check if the specific authentication cookie is present
            auth_cookies = self.session.cookie_jar.filter_cookies(URL(BASE_URL))
            auth_cookie = auth_cookies.get(AUTH_COOKIE_NAME)
            if not auth_cookie:
                raise InvalidAuth("Authentication cookie not found: login re-authentication is required")

            return True
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            raise InvalidAuth("Authentication cookie file not found or invalid")
