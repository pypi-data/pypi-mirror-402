"""Shared test fixtures and configuration."""
import asyncio
import pytest
import aiohttp
from unittest.mock import Mock
import aioresponses


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_session():
    """Create a mock aiohttp ClientSession."""
    session = Mock(spec=aiohttp.ClientSession)
    yield session


@pytest.fixture(autouse=True)
def aio_mock():
    """Create a strict aioresponses mock for HTTP requests."""
    with aioresponses.aioresponses() as mock:
        yield mock
