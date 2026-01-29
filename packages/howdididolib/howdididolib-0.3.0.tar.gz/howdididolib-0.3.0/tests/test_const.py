"""Tests for const module."""
from howdididolib import const


class TestConstants:
    def test_base_url(self):
        """Test BASE_URL constant."""
        assert const.BASE_URL == "https://www.howdidido.com"
        assert const.BASE_URL.startswith("https://")

    def test_login_url(self):
        """Test LOGIN_URL constant."""
        assert const.LOGIN_URL == f"{const.BASE_URL}/Account/Login"
        assert "Login" in const.LOGIN_URL

    def test_booking_url(self):
        """Test BOOKING_URL constant."""
        assert const.BOOKING_URL == f"{const.BASE_URL}/Booking"
        assert "Booking" in const.BOOKING_URL

    def test_home_club_url(self):
        """Test HOME_CLUB_URL constant."""
        assert const.HOME_CLUB_URL == f"{const.BASE_URL}/My/Club"
        assert "Club" in const.HOME_CLUB_URL

    def test_fixtures_path(self):
        """Test FIXTURES_PATH constant."""
        assert const.FIXTURES_PATH == "/My/Fixtures"
        assert const.FIXTURES_PATH.startswith("/")

    def test_auth_cookie_name(self):
        """Test AUTH_COOKIE_NAME constant."""
        assert const.AUTH_COOKIE_NAME == ".ASPXAUTH"
        assert const.AUTH_COOKIE_NAME.startswith(".")

    def test_default_auth_cookie_file(self):
        """Test DEFAULT_AUTH_COOKIE_FILE constant."""
        assert const.DEFAULT_AUTH_COOKIE_FILE == "howdidido_auth_cookie.dat"
        assert const.DEFAULT_AUTH_COOKIE_FILE.endswith(".dat")

    def test_user_agent(self):
        """Test USER_AGENT constant."""
        assert "Mozilla/5.0" in const.USER_AGENT
        assert "Windows NT" in const.USER_AGENT
        assert len(const.USER_AGENT) > 50

    def test_timeout(self):
        """Test TIMEOUT constant."""
        assert isinstance(const.TIMEOUT, int)
        assert const.TIMEOUT == 30
        assert const.TIMEOUT > 0
