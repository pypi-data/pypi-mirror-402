"""Tests for fixtures module."""
import pytest
import httpx
from unittest.mock import Mock
from datetime import date
from howdididolib.fixtures import FixtureClient
from howdididolib.types import Fixture


class TestFixtureClient:
    @pytest.fixture
    def client(self):
        """Create a FixtureClient instance."""
        session = Mock(spec=httpx.AsyncClient)
        return FixtureClient(session)

    @pytest.mark.asyncio
    async def test_get_fixtures_with_url(self, respx_mock):
        """Test getting fixtures when URL is provided."""
        # Sample HTML with fixture table
        fixtures_html = '''
        <html>
        <body>
        <table class="table">
            <tbody>
                <tr>
                    <td>15/01/2024</td>
                    <td>Test Fixture</td>
                    <td>Stableford</td>
                    <td><a data-description="Test description">Details</a></td>
                </tr>
                <tr>
                    <td>22/01/2024</td>
                    <td>Another Fixture</td>
                    <td>Medal</td>
                    <td><a data-description="Another description">Details</a></td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        '''

        route = respx_mock.get("https://www.howdidido.com/My/Fixtures?sectionId=123").respond(
            status_code=200, text=fixtures_html
        )

        async with httpx.AsyncClient() as session:
            client = FixtureClient(session, "/My/Fixtures?sectionId=123")
            fixtures = await client.get()

            assert route.called
            assert len(fixtures) == 2

            fixture1 = fixtures[0]
            assert isinstance(fixture1, Fixture)
            assert fixture1.event_date == date(2024, 1, 15)
            assert fixture1.event_name == "Test Fixture"
            assert fixture1.competition_type == "Stableford"
            assert fixture1.event_description == "Test description"

            fixture2 = fixtures[1]
            assert fixture2.event_date == date(2024, 1, 22)
            assert fixture2.event_name == "Another Fixture"
            assert fixture2.competition_type == "Medal"
            assert fixture2.event_description == "Another description"

    @pytest.mark.asyncio
    async def test_get_fixtures_without_url(self, respx_mock):
        """Test getting fixtures when URL needs to be fetched."""
        # Mock the home club page response
        home_html = '''
        <html>
        <body>
        <div class="panel-footer hidden-xs hidden-sm">
            <a href="/My/Fixtures?sectionId=9999">View upcoming Fixtures</a>
        </div>
        </body>
        </html>
        '''

        # Mock the fixtures page response
        fixtures_html = '''
        <html>
        <body>
        <table class="table">
            <tbody>
                <tr>
                    <td>15/01/2024</td>
                    <td>Test Fixture</td>
                    <td>Stableford</td>
                    <td><a data-description="Test description">Details</a></td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        '''

        route1 = respx_mock.get("https://www.howdidido.com/My/Club").respond(
            status_code=200, text=home_html
        )
        route2 = respx_mock.get("https://www.howdidido.com/My/Fixtures?sectionId=9999").respond(
            status_code=200, text=fixtures_html
        )

        async with httpx.AsyncClient() as session:
            client = FixtureClient(session)
            fixtures = await client.get()

            assert route1.called
            assert route2.called
            assert len(fixtures) == 1
            assert fixtures[0].event_name == "Test Fixture"

    @pytest.mark.asyncio
    async def test_get_fixtures_empty_table(self, respx_mock):
        """Test getting fixtures with empty table."""
        fixtures_html = '''
        <html>
        <body>
        <table class="table">
            <tbody>
            </tbody>
        </table>
        </body>
        </html>
        '''

        route = respx_mock.get("https://www.howdidido.com/My/Fixtures?sectionId=123").respond(
            status_code=200, text=fixtures_html
        )

        async with httpx.AsyncClient() as session:
            client = FixtureClient(session, "/My/Fixtures?sectionId=123")
            fixtures = await client.get()

            assert route.called
            assert len(fixtures) == 0
            assert fixtures == []

    @pytest.mark.asyncio
    async def test_get_fixture_url(self, respx_mock):
        """Test getting fixture URL from home page."""
        home_html = '''
        <div class="panel-footer hidden-xs hidden-sm">
            <a href="/My/Fixtures?sectionId=9999">View upcoming Fixtures</a>
        </div>
        '''

        route = respx_mock.get("https://www.howdidido.com/My/Club").respond(
            status_code=200, text=home_html
        )

        async with httpx.AsyncClient() as session:
            client = FixtureClient(session)
            url = await client._get_fixture_url()

            assert route.called
            assert url == "/My/Fixtures?sectionId=9999"

    @pytest.mark.asyncio
    async def test_get_fixture_url_not_found(self, respx_mock):
        """Test getting fixture URL when link is not found."""
        home_html = '''
        <div class="panel-footer hidden-xs hidden-sm">
            <a href="/some-other-link">Some other link</a>
        </div>
        '''

        route = respx_mock.get("https://www.howdidido.com/My/Club").respond(
            status_code=200, text=home_html
        )

        async with httpx.AsyncClient() as session:
            client = FixtureClient(session)
            url = await client._get_fixture_url()

            assert route.called
            assert url is None
