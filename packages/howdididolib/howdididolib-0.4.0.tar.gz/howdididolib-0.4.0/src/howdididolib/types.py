"""Data types and containers for the How Did I Do library."""
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeAlias, List


class Iterable:
    """Base class to allow iteration over public attributes of a dataclass."""
    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith("__") and not callable(getattr(self, attr)):
                yield attr


@dataclass
class BookedEvent(Iterable):
    """Represents a golf event already booked by the user."""
    event_datetime: datetime
    event_name: str
    players: list[str]


@dataclass
class BookableEvent(Iterable):
    """Represents a competition that is currently or soon-to-be bookable."""
    event_date: date
    event_name: str
    book_from_datetime: datetime
    book_to_datetime: datetime


@dataclass
class Bookings:
    """Container for both booked and bookable events."""
    booked_events: list[BookedEvent]
    bookable_events: list[BookableEvent]


@dataclass
class Fixture(Iterable):
    """Represents an upcoming club fixture/competition."""
    event_date: date
    event_name: str
    competition_type: str
    event_description: str


# Type alias for a list of fixtures
Fixtures: TypeAlias = List[Fixture]
