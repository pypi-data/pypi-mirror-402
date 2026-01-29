# rss_engine.py
import feedparser
import httpx
from fastmcp import Context

async def _fetch_rss_feed(url: str, max_results: int = 5, ctx: Context = None) -> str:
    """
    Read an RSS feed from a URL and return the titles and links of the latest articles.
    Useful for getting news updates or content from blogs.
    """
    try:
        if ctx: await ctx.info(f"Fetching RSS content from: {url}")
        
        # 1. Fetch the raw XML data asynchronously
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            if ctx: await ctx.report_progress(1, 3)
            
            response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            xml_data = response.text
            
        if ctx: await ctx.report_progress(2, 3)

        # 2. Parse the XML string with feedparser 
        # (Parsing is CPU bound, so we don't need await here, it's very fast)
        feed = feedparser.parse(xml_data)
        
        if not feed.entries:
            return "No entries found in the feed, or the feed is invalid."

        results = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "Without title")
            link = entry.get("link", "#")
            summary = entry.get("summary", "No summary available")[:200]
            # Cleaning up some HTML if present in summary
            clean_summary = summary.replace('\n', ' ').strip()
            results.append(f"- **{title}**\n  Link: {link}\n  Info: {clean_summary}...")

        if ctx: await ctx.report_progress(3, 3)

        feed_title = feed.feed.get('title', url)
        output = f"Latest news from {feed_title}:\n\n" + "\n".join(results)
        return output

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code}"
        if ctx: await ctx.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error while getting the feed: {str(e)}"
        if ctx: await ctx.error(error_msg)
        return error_msg
