import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add 'app' folder to the path system while testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../feedflow')))

@pytest.fixture
def valid_rss_xml():
    """Returns an example of a avlid feed RSS with entries."""
    return """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Tech Blog</title>
        <item>
            <title>AI Revolution</title>
            <link>https://example.com/ai</link>
            <description>Exploring the future of AI.</description>
        </item>
    </channel>
    </rss>
    """

@pytest.fixture
def no_entries_rss_xml():
    """Returns an example of a feed RSS with no entries."""
    return """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>Empty Blog</title>
        <link>https://example.com</link>
        <description>Feed with no entries</description>
    </channel>
    </rss>
    """

@pytest.fixture
def mock_ctx():
    """
    Create a mock for the FastMCP Context.
    Considering that the Context methods are asyncronous (await ctx.info...), we use AsyncMock.
    """
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    return ctx

@pytest.fixture
def mock_get_feeds_error(mocker):
    return mocker.patch("feedflow.db.aiosqlite.connect", side_effect=Exception("DB Connection Lost"))

@pytest.fixture
def mock_db_error(mocker):
    return mocker.patch("feedflow.db.aiosqlite.connect", side_effect=Exception("DB Connection Lost"))

class AsyncCM:
    def __init__(self, obj):
        self.obj = obj
    async def __aenter__(self):
        return self.obj
    async def __aexit__(self, *args):
        pass

@pytest.fixture
def mock_get_feeds(mocker):
    def _setup_mock(rows):
        # Il Cursore: fetchall deve essere una coroutine
        mock_cursor = MagicMock()
        mock_cursor.fetchall = mocker.AsyncMock(return_value=rows)
        
        # La Connessione: execute deve restituire un oggetto awaitable per async with
        mock_conn = MagicMock()
        mock_conn.execute = MagicMock(return_value=AsyncCM(mock_cursor))
        
        # La Patch: aiosqlite.connect deve restituire un oggetto awaitable per async with
        # Usiamo side_effect per assicurarci che si comporti come una funzione asincrona
        mocker.patch("feedflow.db.aiosqlite.connect", return_value=AsyncCM(mock_conn))
        
        return mock_conn
    return _setup_mock
