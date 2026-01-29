"""Command Line Interface for the How Did I Do library."""
import asyncio
import logging
from dataclasses import fields

import httpx
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from howdididolib.authentication import AuthenticationClient
from howdididolib.bookings import BookingClient
from howdididolib.const import TIMEOUT
from howdididolib.exceptions import InvalidAuth
from howdididolib.fixtures import FixtureClient

# Initialize Rich console for beautiful terminal output
console = Console()

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.ERROR
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
        force=True,
    )
    # Also ensure the root logger and our logger are at the correct level
    logging.getLogger().setLevel(level)
    logger.setLevel(level)


setup_logging(False)

# Initialize Typer app
app = typer.Typer(
    name="howdidido",
    help="Get golf booking information from the How Did I Do website (https://www.howdidido.com)",
    rich_markup_mode="rich",
)

def create_rich_table(data: list, title: str) -> Table:
    """
    Create a beautifully formatted Rich table from a list of objects or dictionaries.

    Args:
        data: A list of dataclass instances or dictionaries to display.
        title: The title to display at the top of the table.

    Returns:
        Table: A Rich Table object, or None if data is empty.
    """
    if not data:
        return None

    # Calculate index column width based on number of items
    index_width = len(str(len(data)))

    table = Table(title=title, title_style="bold magenta", border_style="blue", header_style="bold cyan")
    table.add_column("#", style="dim", no_wrap=True, width=index_width)

    # Automatically determine columns based on the first item in the data list
    if data:
        first_item = data[0]
        if hasattr(first_item, '__dataclass_fields__'):
            # It's a dataclass, use field names
            field_names = [field.name for field in fields(first_item)]
        else:
            # Fallback for dictionaries
            field_names = list(first_item.keys()) if hasattr(first_item, 'keys') else []

        for field_name in field_names:
            table.add_column(field_name.replace('_', ' ').title(), style="white")

    # Populate rows with data
    for i, item in enumerate(data, 1):
        if hasattr(item, '__dataclass_fields__'):
            values = []
            for field in fields(item):
                value = str(getattr(item, field.name))
                values.append(value)
        else:
            # Fallback for dictionaries
            values = [str(value) for value in item.values()] if hasattr(item, 'values') else []

        table.add_row(f"{i}", *values)

    return table


async def get_session(debug: bool = False) -> httpx.AsyncClient:
    """
    Create and return an httpx AsyncClient with optional debug logging hooks.

    Args:
        debug: If True, attaches logging hooks to print raw request and response data.
    """
    if debug:

        async def log_request(request):
            logging.debug(f"> {request.method} {request.url}")
            for k, v in request.headers.items():
                logging.debug("> %s: %s", k, v)

        async def log_response(response):
            request = response.request
            logging.debug(f"< {request.method} {request.url} {response.status_code}")
            for k, v in response.headers.items():
                logging.debug("< %s: %s", k, v)
            try:
                # Ensure the response content is read before attempting to access .text
                await response.aread()
                logging.debug("< %s", response.text)
            except Exception:
                logging.debug("< [Response body not available]")

        return httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
            event_hooks={'request': [log_request], 'response': [log_response]},
        )
    else:
        return httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True)


@app.command()
def auth(
    username: str = typer.Option(..., help="Username for authentication", prompt=True),
    password: str = typer.Option(
        ..., help="Password for authentication", prompt=True, hide_input=True
    ),
    debug: bool = typer.Option(False, help="Enable debug logging"),
) -> None:
    """🔐 Authenticate with How Did I Do and save credentials locally."""
    setup_logging(debug)

    async def _auth():
        with console.status("[bold green]🔐 Authenticating...", spinner="dots") as status:
            session = await get_session(debug)
            async with session:
                auth_client = AuthenticationClient(session, username=username, password=password)
                try:
                    await auth_client.login()
                    status.update("[bold green]💾 Saving credentials...")
                    await auth_client.save_auth_cookie()

                    success_panel = Panel.fit(
                        f"✅ [bold green]Authentication successful![/bold green]\n"
                        f"👤 User: [cyan]{username}[/cyan]\n"
                        f"💾 Credentials saved for future use",
                        title="🎉 Success",
                        border_style="green",
                        padding=(1, 2)
                    )
                    console.print(success_panel)

                except (httpx.HTTPError, InvalidAuth) as e:
                    error_panel = Panel.fit(
                        f"❌ [bold red]Authentication failed[/bold red]\n\n{str(e)}",
                        title="🚫 Error",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    raise typer.Exit(1)

    # Run the async logic using asyncio.run
    asyncio.run(_auth())


@app.command()
def bookings(
    debug: bool = typer.Option(False, help="Enable debug logging"),
) -> None:
    """📅 Retrieve and display your golf booking information."""
    setup_logging(debug)

    async def _bookings():
        with console.status("[bold blue]🔐 Restoring authentication...", spinner="dots") as status:
            session = await get_session(debug)
            async with session:
                auth_client = AuthenticationClient(session)
                try:
                    # Attempt to reload saved cookies
                    await auth_client.restore_auth_cookie()

                    status.update("[bold blue]📅 Fetching booking data...")
                    booking_client = BookingClient(session)
                    bookings_data = await booking_client.get()

                    status.update("[bold blue]🎨 Formatting results...")

                    # Display booked events if any exist
                    if bookings_data.booked_events:
                        table = create_rich_table(bookings_data.booked_events, title="🎯 Booked Events")
                        console.print(table)
                        console.print()

                    # Display events available for booking if any exist
                    if bookings_data.bookable_events:
                        table = create_rich_table(bookings_data.bookable_events, title="📋 Bookable Events")
                        console.print(table)
                        console.print()

                    # Handle case where no data was returned
                    if not bookings_data.booked_events and not bookings_data.bookable_events:
                        empty_panel = Panel.fit(
                            "📭 [dim]No bookings found[/dim]",
                            title="📅 Bookings",
                            border_style="blue",
                            padding=(1, 2)
                        )
                        console.print(empty_panel)

                except InvalidAuth:
                    error_panel = Panel.fit(
                        "❌ [bold red]No saved credentials found[/bold red]\n\n"
                        "Please run [cyan]'howdidido auth'[/cyan] first to authenticate.",
                        title="🚫 Authentication Required",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    raise typer.Exit(1)
                except httpx.HTTPError as e:
                    error_panel = Panel.fit(
                        f"❌ [bold red]Failed to fetch bookings[/bold red]\n\n{str(e)}",
                        title="🚫 Error",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    raise typer.Exit(1)

    asyncio.run(_bookings())


@app.command()
def fixtures(
    debug: bool = typer.Option(False, help="Enable debug logging"),
) -> None:
    """🏟️ Retrieve and display upcoming golf fixtures."""
    setup_logging(debug)

    async def _fixtures():
        with console.status("[bold purple]🔐 Restoring authentication...", spinner="dots") as status:
            session = await get_session(debug)
            async with session:
                auth_client = AuthenticationClient(session)
                try:
                    await auth_client.restore_auth_cookie()

                    status.update("[bold purple]🏟️ Fetching fixture data...")
                    fixture_client = FixtureClient(session)
                    fixtures_data = await fixture_client.get()

                    status.update("[bold purple]🎨 Formatting results...")

                    if fixtures_data:
                        table = create_rich_table(fixtures_data, title="🏟️ Fixtures")
                        console.print(table)
                    else:
                        empty_panel = Panel.fit(
                            "🏟️ [dim]No fixtures found[/dim]",
                            title="🏟️ Fixtures",
                            border_style="purple",
                            padding=(1, 2)
                        )
                        console.print(empty_panel)

                except InvalidAuth:
                    error_panel = Panel.fit(
                        "❌ [bold red]No saved credentials found[/bold red]\n\n"
                        "Please run [cyan]'howdidido auth'[/cyan] first to authenticate.",
                        title="🚫 Authentication Required",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    raise typer.Exit(1)
                except httpx.HTTPError as e:
                    error_panel = Panel.fit(
                        f"❌ [bold red]Failed to fetch fixtures[/bold red]\n\n{str(e)}",
                        title="🚫 Error",
                        border_style="red",
                        padding=(1, 2)
                    )
                    console.print(error_panel)
                    raise typer.Exit(1)

    asyncio.run(_fixtures())


if __name__ == '__main__':
    # Directly invoke the Typer app if executed as a script
    app()


def sync_main() -> int:
    """
    Synchronous entry point for the console script.

    Provides high-level exception handling and returns appropriate exit codes.
    """
    try:
        app()
        return 0
    except typer.Exit as e:
        return e.exit_code
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
        return 1
