# tests/tests_rss_engine.py
import pytest
import httpx
from feedflow.rss_engine import _fetch_rss_feed

pytestmark = pytest.mark.asyncio

async def test_fetch_rss_feed(respx_mock, valid_rss_xml):
    """Test successful feed retrieval with entries."""
    url = "https://example.com/feed.xml"

    respx_mock.get(url).mock(return_value=httpx.Response(200, text=valid_rss_xml))
        
    result = await _fetch_rss_feed(url)
    
    assert "Latest news from Tech Blog" in result
    assert "**AI Revolution**" in result
    assert "Link: https://example.com/ai" in result

     
async def test_fetch_rss_feed_no_entries(respx_mock, no_entries_rss_xml):
    url = "https://example.com/empty-feed.xml"
    
    respx_mock.get(url).mock(return_value=httpx.Response(200, text=no_entries_rss_xml))
        
    result_msg = await _fetch_rss_feed(url)
    
    assert "No entries found in the feed, or the feed is invalid." in result_msg

async def test_fetch_rss_feed_general_error(respx_mock):
    url = "https://server-inexistent.com/rss"
    
    respx_mock.get(url).mock(side_effect=httpx.ConnectError("Network is unreachable"))
        
    result_msg = await _fetch_rss_feed(url)
    
    assert "Error while getting the feed" in result_msg
    assert "Network is unreachable" in result_msg
        
async def test_fetch_rss_feed_http_error(respx_mock):
    url = "https://fake-url.com/feed"
    
    respx_mock.get(url).mock(return_value=httpx.Response(404))
        
    result_msg = await _fetch_rss_feed(url)
    
    assert "HTTP error occurred: 404" in result_msg

async def test_fetch_rss_complete_flow(respx_mock, mock_ctx, valid_rss_xml):
    """
    This test uses 3 fixtures:
    1. respx_mock: to intercept the HTTP requests (provided internally by respx)
    2. mock_ctx: to verify the context progress/log (from conftest.py)
    3. valid_rss_xml: valid xml test (from conftest.py)
    """
    url = "https://example.com/feed.xml"
    
    respx_mock.get(url).mock(return_value=httpx.Response(200, text=valid_rss_xml))
    
    result = await _fetch_rss_feed(url, ctx=mock_ctx)
    
    assert "Latest news from Tech Blog" in result
    
    mock_ctx.info.assert_called_with(f"Fetching RSS content from: {url}")
    mock_ctx.report_progress.assert_called()
