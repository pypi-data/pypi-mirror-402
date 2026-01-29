"""Fixtures module for retrieving upcoming golf competition information."""

import logging
from datetime import datetime

import aiohttp
import bs4

from howdididolib.const import HOME_CLUB_URL, USER_AGENT, BASE_URL
from howdididolib.types import Fixture, Fixtures

logger = logging.getLogger(__name__)


class FixtureClient:
    """Client for retrieving and parsing upcoming club fixtures."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        fixture_url: str = None
    ):
        """
        Initialize the fixture client.

        Args:
            session: The aiohttp ClientSession to use for requests.
            fixture_url: Optional override for the fixture page URL.
        """
        self.session = session
        self.fixture_url = fixture_url

    async def get(self) -> Fixtures:
        """
        Fetch and parse the list of upcoming fixtures.

        Returns:
            Fixtures: A list of Fixture objects.

        Raises:
            aiohttp.ClientError: If there is a network error.
        """
        # Automatically discover the fixtures URL if not provided
        if not self.fixture_url:
            self.fixture_url = await self._get_fixture_url()

        async with self.session.get(
            f"{BASE_URL}{self.fixture_url}",
            headers={
                "user-agent": USER_AGENT,
            },
        ) as resp:
            resp.raise_for_status()
            soup = bs4.BeautifulSoup(await resp.text(), "html.parser")

        # Parse the fixtures table
        table = soup.find("table", attrs={"class": "table"})
        if not table:
            return []

        table_body = table.find('tbody')
        if not table_body:
            return []

        rows = table_body.find_all('tr')

        fixture_events = []

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue

            event_date, event_name, competition_type, event_description = cols

            fixture_events.append(
                Fixture(
                    event_date=datetime.strptime(event_date.text.strip(), "%d/%m/%Y").date(),
                    event_name=event_name.text.strip(),
                    competition_type=competition_type.text.strip(),
                    event_description=event_description.a["data-description"].strip()
                )
            )

        return fixture_events

    async def _get_fixture_url(self) -> str:
        """
        Scrape the club home page to find the specific link to the fixtures page.
        """

        async with self.session.get(
            HOME_CLUB_URL,
            headers={
                "user-agent": USER_AGENT,
            },
        ) as resp:
            resp.raise_for_status()
            soup = bs4.BeautifulSoup(await resp.text(), "html.parser")

        # Locate the "View upcoming Fixtures" link in the footer
        fixture_link = soup.find(lambda tag: tag.name == "a" and "View upcoming Fixtures" in tag.text)

        return fixture_link['href'] if fixture_link else None
