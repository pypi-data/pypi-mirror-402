"""Tests for bookings module."""
import pytest
import aiohttp
from unittest.mock import Mock
from datetime import datetime, date
from howdididolib.bookings import BookingClient, _format_date_string
from howdididolib.types import Bookings


class TestBookingClient:
    @pytest.fixture
    def client(self):
        """Create a BookingClient instance."""
        session = Mock(spec=aiohttp.ClientSession)
        return BookingClient(session)

    @pytest.mark.asyncio
    async def test_get_bookings(self, aio_mock):
        """Test getting bookings with sample HTML."""
        # Sample HTML with booked and bookable events
        bookings_html = '''
        <html>
        <body>
        <div id="upcoming-bookings-container">
            <div class="cb">
                <div class="date-time theme_bg">
                    <div class="wday">Sun</div>
                    <div class="date">15 Jan</div>
                    <div class="time">09:16</div>
                </div>
                <div class="info">
                    <div class="name">
                        <a href="/link" target="_blank" class="theme_hover_text">Men's January Stableford 2</a>
                    </div>
                    <div class="players">
                        <div class="player col-xs-12 col-sm-6">
                            <span class="pos">P1</span>
                            <span>JOHN SMITH</span>
                        </div>
                        <div class="player col-xs-12 col-sm-6">
                            <span class="pos">P2</span>
                            <span>JOHNNY WALKER</span>
                        </div>
                        <div class="player col-xs-12 col-sm-6">
                            <span class="pos">P3</span>
                            <span>DAVID PALMER</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div id="comp-booking-selector">
            <div class="cb">
                <div class="date-time theme_bg">
                    <div class="wday">Sun</div>
                    <div class="date">28 Dec</div>
                    <div class="time"></div>
                </div>
                <div class="info">
                    <div class="name">
                        <a href="/link" class="theme_hover_text">
                            <i class="fa fa-trophy"></i><span>Men's February Medal</span>
                        </a>
                    </div>
                    <div class="comp-info">
                        <div class="book-from-until">
                            <div class="from">
                                <span class="lbl-from">Book From</span>
                                <span class="val">25th Dec 2024 07:00</span>
                            </div>
                            <div class="to">
                                <span class="lbl-to">To</span>
                                <span class="val">19th Jan 2025 18:00</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </body>
        </html>
        '''

        aio_mock.get("https://www.howdidido.com/Booking", status=200, body=bookings_html.strip())

        async with aiohttp.ClientSession() as session:
            client = BookingClient(session)
            bookings = await client.get()

            assert isinstance(bookings, Bookings)
            assert len(bookings.booked_events) == 1
            assert len(bookings.bookable_events) == 1

            # Check booked event
            booked = bookings.booked_events[0]
            assert booked.event_name == "Men's January Stableford 2"
            assert booked.players == ["JOHN SMITH", "JOHNNY WALKER", "DAVID PALMER"]
            assert isinstance(booked.event_datetime, datetime)

            # Check bookable event
            bookable = bookings.bookable_events[0]
            assert bookable.event_name == "Men's February Medal"
            assert isinstance(bookable.event_date, date)
            assert isinstance(bookable.book_from_datetime, datetime)
            assert isinstance(bookable.book_to_datetime, datetime)

    @pytest.mark.asyncio
    async def test_get_bookings_empty(self, aio_mock):
        """Test getting bookings with no events."""
        bookings_html = '''
        <div id="upcoming-bookings-container"></div>
        <div id="comp-booking-selector"></div>
        '''

        aio_mock.get("https://www.howdidido.com/Booking", status=200, body=bookings_html)

        async with aiohttp.ClientSession() as session:
            client = BookingClient(session)
            bookings = await client.get()

            assert isinstance(bookings, Bookings)
            assert len(bookings.booked_events) == 0
            assert len(bookings.bookable_events) == 0

    @pytest.mark.asyncio
    async def test_get_bookings_past_date(self, aio_mock):
        """Test getting bookings with a date that has already passed this year."""
        # Using "1 Jan" which should be parsed as Jan 1, current_year.
        # Since today is Jan 19, 2026, it should add 365 days to it.
        bookings_html = '''
        <div id="comp-booking-selector">
            <div class="cb">
                <div class="date-time theme_bg">
                    <div class="date">1 Jan</div>
                </div>
                <div class="info">
                    <div class="name">
                        <a href="/link" class="theme_hover_text">
                            <i class="fa fa-trophy"></i><span>Past Event</span>
                        </a>
                    </div>
                    <div class="comp-info">
                        <div class="book-from-until">
                            <div class="from">
                                <span class="lbl-from">Book From</span>
                                <span class="val">25th Dec 2024 07:00</span>
                            </div>
                            <div class="to">
                                <span class="lbl-to">To</span>
                                <span class="val">19th Jan 2025 18:00</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''

        aio_mock.get("https://www.howdidido.com/Booking", status=200, body=bookings_html)

        async with aiohttp.ClientSession() as session:
            client = BookingClient(session)
            bookings = await client.get()

            assert len(bookings.bookable_events) == 1
            # Current year is 2026. 1 Jan matches 1 Jan 2026.
            # 1 Jan 2026 < 19 Jan 2026, so it becomes 1 Jan 2027.
            assert bookings.bookable_events[0].event_date.year == datetime.now().year + 1


class TestFormatDateString:
    def test_format_date_string_simple(self):
        """Test _format_date_string with simple date."""
        result = _format_date_string("21 Jan")
        assert result == "21 01"

    def test_format_date_string_with_ordinal(self):
        """Test _format_date_string with ordinal numbers."""
        result = _format_date_string("25th Dec 2023 07:00")
        assert result == "25 12 2023 07:00"

    def test_format_date_string_multiple_ordinals(self):
        """Test _format_date_string with multiple ordinals."""
        result = _format_date_string("1st Jan 2024 09:00")
        assert result == "1 01 2024 09:00"

    def test_format_date_string_no_month(self):
        """Test _format_date_string with no month name."""
        result = _format_date_string("2024-01-15")
        assert result == "2024-01-15"

    def test_format_date_string_all_months(self):
        """Test _format_date_string with all month abbreviations."""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        numbers = ['01', '02', '03', '04', '05', '06',
                  '07', '08', '09', '10', '11', '12']

        for month, number in zip(months, numbers):
            result = _format_date_string(f"15 {month} 2024")
            assert result == f"15 {number} 2024"
