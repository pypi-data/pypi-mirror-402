# tests/test_db.py
import pytest
import aiosqlite
from unittest.mock import AsyncMock

# Integration Tests

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

import feedflow.db as db_module

@pytest.fixture
async def setup_database(tmp_path, monkeypatch):
    """
    Fixture to set up a temporary in-memory database for testing.
    This runs before each test function that uses it.
    """
    # Create a temporary database file
    temp_db_path = tmp_path / "test_feeds.db"
    
    # Use monkeypatch to temporarily change the DB_PATH in the db module
    monkeypatch.setattr('feedflow.db.DB_PATH', temp_db_path)
    
    # Initialize the database schema
    await db_module.init_db()
    
    # Yield the path to the database for tests to use
    yield temp_db_path
    
    # Teardown (cleanup) is handled automatically by tmp_path fixture


async def test_init_db(setup_database):
    """
    Tests if the database and the 'feeds' table are created correctly.
    """
    db_path = setup_database
    assert db_path.exists()
    
    async with aiosqlite.connect(db_path) as db:
        # Check if 'feeds' table exists
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feeds'") as cursor:
            result = await cursor.fetchone()
            assert result is not None, "The 'feeds' table was not created."
        
        # Check if the table has the correct columns
        async with db.execute("PRAGMA table_info(feeds)") as cursor:
            columns = {row[1] for row in await cursor.fetchall()}
            expected_columns = {'id', 'name', 'url', 'category', 'language'}
            assert columns == expected_columns, "The 'feeds' table has incorrect columns."
            
        # Check if the index on 'category' exists
        async with db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_category'") as cursor:
            result = await cursor.fetchone()
            assert result is not None, "The index on 'category' was not created."


async def test_add_feed(setup_database):
    """
    Tests adding a feed to the database.
    """
    result_msg = await db_module._add_feed(
        name="TechCrunch",
        url="https://techcrunch.com/feed/",
        category="Tech",
        lang="en"
    )
    
    assert result_msg == "Successfully added 'TechCrunch' to the Tech category."
    
    async with aiosqlite.connect(setup_database) as db:
        async with db.execute("SELECT name, url, category, language FROM feeds WHERE name = 'TechCrunch'") as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == "TechCrunch"
            assert row[1] == "https://techcrunch.com/feed/"
            assert row[2] == "Tech"
            assert row[3] == "en"

async def test_remove_feed(setup_database):
    async with aiosqlite.connect(setup_database) as db:
        await db_module._add_feed("Test", "https://test.com", "Tech", "en")
    
    assert await db_module._remove_feed("https://test.com") is True
    assert await db_module._remove_feed("https://test.com") is False
    
async def test_get_feeds_empty(setup_database):
    """
    Tests getting feeds when the database is empty.
    """
    result = await db_module._get_feeds()
    assert result == "No feeds configured. Use the 'add_feed' tool to add some!"


async def test_get_feeds_with_data(setup_database):
    """
    Tests getting all feeds and feeds filtered by category.
    """
    await db_module._add_feed("Feed 1", "url1", "Cat A", "en")
    await db_module._add_feed("Feed 2", "url2", "Cat B", "es")
    await db_module._add_feed("Feed 3", "url3", "Cat A", "fr")
    
    # Test getting all feeds
    all_feeds = await db_module._get_feeds()
    assert "Feed 1" in all_feeds
    assert "[Cat A]" in all_feeds
    assert "Feed 2" in all_feeds
    assert "[Cat B]" in all_feeds
    
    # Test filtering by an existing category
    cat_a_feeds = await db_module._get_feeds(category="Cat A")
    assert "Feed 1" in cat_a_feeds
    assert "Feed 3" in cat_a_feeds
    assert "Feed 2" not in cat_a_feeds
    assert "[Cat A]" not in cat_a_feeds # Category is not in the output when filtered
    
    # Test filtering by a non-existent category
    cat_c_feeds = await db_module._get_feeds(category="Cat C")
    assert cat_c_feeds == "No feeds found in the 'Cat C' category."


async def test_get_categories(setup_database):
    """
    Tests retrieving unique categories from the database.
    """
    # Test with no categories
    categories = await db_module._get_categories()
    assert categories == []
    
    # Add data and test again
    await db_module._add_feed("Feed 1", "url1", "Tech", "en")
    await db_module._add_feed("Feed 2", "url2", "AI", "en")
    await db_module._add_feed("Feed 3", "url3", "Tech", "en") # Duplicate category
    
    categories = await db_module._get_categories()
    assert len(categories) == 2
    # Sort for consistent comparison
    assert sorted(categories) == ["AI", "Tech"]

# Mocking tests
async def test_get_feeds_exception_mock(mock_get_feeds_error):
    result = await db_module._get_feeds(ctx=None, category=None)
    
    assert "Error while getting feeds: DB Connection Lost" in result

async def test_add_feed_exception_mock(mock_db_error):
    result = await db_module._add_feed("Test", "https://test.com", "Tech", "en", ctx=None)
     
    assert "Error adding feed:" in result
    
async def test_remove_feed_ctx_mock(mock_db_error):
    result = await db_module._remove_feed("https://test.com", ctx=None)
     
    assert result is False
        
async def test_get_feeds_ctx_mock(mock_get_feeds):
    fake_data = [
        ("Tech News", "https://tech.com/rss", "Technology"),
        ("Sport News", "https://sport.com/rss", "Sport")
    ]
    mock_get_feeds(fake_data)
    
    mock_ctx = AsyncMock()

    rows_output = await db_module._get_feeds(ctx=mock_ctx, category=None)

    print(f"\nDEBUG RESULT: {rows_output}")

    mock_ctx.info.assert_any_call("Collected 2 feed with success.")
    mock_ctx.report_progress.assert_any_call(5, 5)

    assert "Tech News" in rows_output
