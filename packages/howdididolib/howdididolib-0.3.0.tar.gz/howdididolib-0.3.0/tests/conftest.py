"""Shared test fixtures and configuration."""
import asyncio
import pytest
import httpx
from unittest.mock import Mock
import respx


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_session():
    """Create a mock httpx AsyncClient."""
    session = Mock(spec=httpx.AsyncClient)
    yield session


@pytest.fixture(autouse=True)
def respx_mock():
    """Create a strict respx mock for HTTP requests."""
    with respx.mock(assert_all_called=False) as mock:
        yield mock
