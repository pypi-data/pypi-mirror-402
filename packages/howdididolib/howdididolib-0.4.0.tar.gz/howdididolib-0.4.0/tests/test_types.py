"""Tests for types module."""
from datetime import date, datetime
from howdididolib.types import BookedEvent, BookableEvent, Bookings, Fixture


class TestBookedEvent:
    def test_creation(self):
        """Test BookedEvent dataclass creation."""
        event_datetime = datetime(2024, 1, 15, 10, 30)
        event_name = "Test Event"
        players = ["Player 1", "Player 2"]

        event = BookedEvent(event_datetime, event_name, players)

        assert event.event_datetime == event_datetime
        assert event.event_name == event_name
        assert event.players == players

    def test_iterable(self):
        """Test that BookedEvent is iterable."""
        event = BookedEvent(
            datetime(2024, 1, 15, 10, 30),
            "Test Event",
            ["Player 1", "Player 2"]
        )

        attrs = list(event)
        assert "event_datetime" in attrs
        assert "event_name" in attrs
        assert "players" in attrs


class TestBookableEvent:
    def test_creation(self):
        """Test BookableEvent dataclass creation."""
        event_date = date(2024, 1, 15)
        event_name = "Test Event"
        book_from = datetime(2024, 1, 10, 9, 0)
        book_to = datetime(2024, 1, 14, 18, 0)

        event = BookableEvent(event_date, event_name, book_from, book_to)

        assert event.event_date == event_date
        assert event.event_name == event_name
        assert event.book_from_datetime == book_from
        assert event.book_to_datetime == book_to

    def test_iterable(self):
        """Test that BookableEvent is iterable."""
        event = BookableEvent(
            date(2024, 1, 15),
            "Test Event",
            datetime(2024, 1, 10, 9, 0),
            datetime(2024, 1, 14, 18, 0)
        )

        attrs = list(event)
        assert "event_date" in attrs
        assert "event_name" in attrs
        assert "book_from_datetime" in attrs
        assert "book_to_datetime" in attrs


class TestBookings:
    def test_creation(self):
        """Test Bookings dataclass creation."""
        booked_events = [
            BookedEvent(datetime(2024, 1, 15, 10, 30), "Event 1", ["P1", "P2"])
        ]
        bookable_events = [
            BookableEvent(date(2024, 1, 20), "Event 2",
                         datetime(2024, 1, 15, 9, 0), datetime(2024, 1, 19, 18, 0))
        ]

        bookings = Bookings(booked_events, bookable_events)

        assert bookings.booked_events == booked_events
        assert bookings.bookable_events == bookable_events

    def test_empty_creation(self):
        """Test Bookings with empty lists."""
        bookings = Bookings([], [])

        assert bookings.booked_events == []
        assert bookings.bookable_events == []


class TestFixture:
    def test_creation(self):
        """Test Fixture dataclass creation."""
        event_date = date(2024, 1, 15)
        event_name = "Test Fixture"
        competition_type = "Stableford"
        event_description = "Test description"

        fixture = Fixture(event_date, event_name, competition_type, event_description)

        assert fixture.event_date == event_date
        assert fixture.event_name == event_name
        assert fixture.competition_type == competition_type
        assert fixture.event_description == event_description

    def test_iterable(self):
        """Test that Fixture is iterable."""
        fixture = Fixture(
            date(2024, 1, 15),
            "Test Fixture",
            "Stableford",
            "Test description"
        )

        attrs = list(fixture)
        assert "event_date" in attrs
        assert "event_name" in attrs
        assert "competition_type" in attrs
        assert "event_description" in attrs
