"""Tests for console module."""
import aiohttp
import pytest
from datetime import datetime, date
from howdididolib.console import create_rich_table
from howdididolib.types import BookedEvent, Fixture
from rich.table import Table


class TestCreateRichTable:
    def test_create_table_with_dataclass(self):
        """Test creating table with dataclass objects."""
        events = [
            BookedEvent(
                datetime(2024, 1, 15, 10, 30),
                "Event 1",
                ["Player 1", "Player 2"]
            ),
            BookedEvent(
                datetime(2024, 1, 16, 14, 0),
                "Event 2",
                ["Player 3"]
            )
        ]

        table = create_rich_table(events, "Test Events")

        assert isinstance(table, Table)
        assert table.title == "Test Events"
        assert "Event Datetime" in table.columns[1].header
        assert "Event Name" in table.columns[2].header
        assert "Players" in table.columns[3].header

    def test_create_table_with_fixture(self):
        """Test creating table with Fixture objects."""
        fixtures = [
            Fixture(
                date(2024, 1, 15),
                "Fixture 1",
                "Stableford",
                "Description 1"
            )
        ]

        table = create_rich_table(fixtures, "Test Fixtures")

        assert isinstance(table, Table)
        assert table.title == "Test Fixtures"
        assert "Event Date" in table.columns[1].header
        assert "Event Name" in table.columns[2].header
        assert "Competition Type" in table.columns[3].header
        assert "Event Description" in table.columns[4].header

    def test_create_table_empty(self):
        """Test creating table with empty data."""
        table = create_rich_table([], "Empty Table")

        assert table is None

    def test_create_table_with_dict_fallback(self):
        """Test creating table with dict-like objects (fallback)."""
        data = [
            {"name": "Item 1", "value": "100"},
            {"name": "Item 2", "value": "200"}
        ]

        table = create_rich_table(data, "Dict Table")

        assert isinstance(table, Table)
        assert table.title == "Dict Table"
        assert "Name" in table.columns[1].header
        assert "Value" in table.columns[2].header


class TestGetSession:
    @pytest.mark.asyncio
    async def test_get_session_normal(self):
        """Test get_session without debug."""
        from howdididolib.console import get_session

        session = await get_session(debug=False)

        assert isinstance(session, aiohttp.ClientSession)
        await session.close()

    @pytest.mark.asyncio
    async def test_get_session_debug(self):
        """Test get_session with debug enabled."""
        from howdididolib.console import get_session

        session = await get_session(debug=True)

        assert isinstance(session, aiohttp.ClientSession)
        await session.close()
