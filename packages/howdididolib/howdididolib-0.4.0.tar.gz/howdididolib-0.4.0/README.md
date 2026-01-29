# How Did I Do Library

A Python library and CLI tool for retrieving golf booking and fixture information from the [How Did I Do](https://www.howdidido.com) website.

## Features

- 🔐 **Secure Authentication**: Authenticate once and save credentials locally.
- 📅 **Booking Information**: Retrieve details of both your current and upcoming bookable golf events.
- 🏟️ **Fixtures**: Get a comprehensive list of upcoming fixtures and competitions.
- 💻 **CLI Interface**: Easy-to-use command-line interface with `rich` formatting.
- 🧪 **High Coverage**: Robust test suite with 99% coverage.

## Installation

Install using `uv`:

```shell
uv add howdididolib
```

Or using `pip`:

```shell
pip install howdididolib
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for package management.

### Setup

```shell
# Install dependencies
uv sync
```

### Running Tests

```shell
uv run pytest
```

## CLI Usage

The library includes a CLI tool named `howdidido`.

### Authentication

First, authenticate and save your credentials:

```shell
uv run howdidido auth --username "your_username" --password "your_password"
```

### Get Bookings

View your current and upcoming bookable events:

```shell
uv run howdidido bookings
```

### Get Fixtures

View upcoming fixtures:

```shell
uv run howdidido fixtures
```

### Debugging

Enable verbose logging for any command:

```shell
uv run howdidido bookings --debug
```

## Programmatic Usage

You can also use the library in your own Python projects:

```python
import aiohttp
from howdididolib.authentication import AuthenticationClient
from howdididolib.bookings import BookingClient

async def main():
    async with aiohttp.ClientSession() as session:
        auth = AuthenticationClient(session, username="user", password="pass")
        await auth.login()
        await auth.save_auth_cookie()

        booking_client = BookingClient(session)
        bookings = await booking_client.get()
        print(bookings.booked_events)
```

## License

Distributed under the MIT License. See `LICENSE` for more information.
