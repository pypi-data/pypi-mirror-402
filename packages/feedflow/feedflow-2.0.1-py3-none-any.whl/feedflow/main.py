import logging
import sys
from importlib.metadata import version, PackageNotFoundError
from fastmcp import FastMCP, Context
from mcp.types import PromptMessage, TextContent
from pydantic import TypeAdapter, HttpUrl, Field
from typing import Optional
try: 
    from .db import _add_feed, _get_feeds, init_db, _get_categories, _remove_feed
    from .rss_engine import _fetch_rss_feed
except (ImportError, ValueError):# pragma: no cover
    from db import _add_feed, _get_feeds, init_db, _get_categories, _remove_feed # pragma: no cover
    from rss_engine import _fetch_rss_feed  # pragma: no cover

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Get version from metadata (the name must match the one in pyproject.toml)
try:
    __version__ = version("feedflow")
except PackageNotFoundError:
    # Fallback if the package is not installed (e.g., during local development)
    __version__ = "0.0.0-dev" # pragma: no cover
    
# Init the server
mcp = FastMCP(
    name="FeedFlow",
    version=__version__,
    instructions="""
        This stdio mcp help getting feeds summary.
    """
)

# --- RESOURCES ---
@mcp.resource("feeds://feeds", name="All RSS Feeds") 
def get_feeds() -> str: # pragma: no cover
    """
    Returns the list of all RSS feeds.
    The AI can use these URLs with the fetch_rss_feed tool.
    """
    return _get_feeds()

@mcp.resource("feeds://categories", name="List Feeds' Categories")
async def get_feeds_categories() -> str: # pragma: no cover
    """
    Returns a list of all unique categories available in the database.
    This helps the AI know which categories can be used in resource templates.
    """
    categories = await _get_categories()
    
    if not categories:
        return "No categories found in the database."
    
    return "Available categories:\n" + "\n".join(f"- {cat}" for cat in categories)

@mcp.resource("feeds://feeds/{category}", name="Feeds by Category")
def get_feeds_by_category(category: str) -> str: # pragma: no cover
    """
    Returns a list of RSS feeds filtered by category.
    Check feeds://categories for a list of valid categories.
    """
    return _get_feeds(category=category)

# --- Prompts ---
@mcp.prompt(
        name="available_feeds_categories",
        description="Get available feeds unique categories"
)
async def available_feeds_categories() -> list[PromptMessage]: # pragma: no cover
    prompt_text = f"""
    List the unique categories available in the database.
    You can use the resource feeds://categories
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_text)
        )
    ]

@mcp.prompt(
        name="latest_news_by_category",
        description="Get lastest news by category"
)
async def latest_news_by_category(
    category: str = Field(None, description="Get the latest news from a specific category. Only get the very latest one for each feed in the provided category.")
) -> list[PromptMessage]: # pragma: no cover
    prompt_text = f"""
    Get the Feeds list for the selected category: {category}. You can use the resource: feeds://feeds/category or the tool list_feeds.
    Once you get the list of feeds for the selected category. Go through each one and get only 1 (the most recent) news.
    Finally provide back the answer listing all the collected news, indicating the source feed title and url too
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_text)
        )
    ]

@mcp.prompt(
        name="latest_news_by_argument",
        description="Get lastest news by argument"
)
async def latest_news_by_argument(
    argument: str = Field(None, description="Get the latest news from a specific argument. Only get the very latest one for each feed related with the argument."),
    max_results: int = Field(default=1, ge=1, le=10, description="Number of articles to fetch.")
) -> list[PromptMessage]: # pragma: no cover
    prompt_text = f"""
    Considering the following argument: {argument}, get only the feeds related with it.
    To get the feeds list use the tool list_feeds.
    Once you get the list of feeds choose only the ones that relate to the argument.
    Then Go through each one and get only the {max_results} most recent news.
    Finally provide back the answer listing all the collected news, indicating the source feed title and url too
    """
    return [
        PromptMessage(
            role="user",
            content=TextContent(type="text", text=prompt_text)
        )
    ]

# --- TOOLS ---
@mcp.tool()
async def add_feed(
    url: str,
    name: str = Field(..., description="The name of the feed. If no name or title is provided use the website domain name from the provided url"),
    category: str = "General",
    lang: str = Field('en', description="The language of the feed as an ISO 639-1 code (2 lowercase letters). Try to detect from the feed content."
                "Examples: 'en' for English, 'it' for Italian, 'es' for Spanish. "
                "If the language cannot be determined, default to 'en'."
            ),
    ctx: Context = None
) -> str: # pragma: no cover
    """Adds a new RSS feed to the Feeds list persistently."""
    try:
        TypeAdapter(HttpUrl).validate_python(url)
    except Exception as e:
        if ctx: await ctx.error(f"Invalid URL: {str(e)}")
        return f"Error adding feed: {str(e)}"
    
    return await _add_feed(name, url, category, lang, ctx)

@mcp.tool()
async def remove_feed(
    feed: str = Field(None, description="The name or the url of the feed to remove from the Database. To be sure about it, before to delete get the list of the feeds with the list_feeds tool."),
    ctx: Context = None
) -> str: # pragma: no cover
    """
    Remove a feed from the Database
    """
    success = await _remove_feed(feed, ctx)
    
    if success:
        return f"Successfully removed feed: {feed}"
    else:
        return f"No feed found matching '{feed}'. Check the list of feeds for the exact name or URL."
    
@mcp.tool()
async def list_feeds(
    ctx: Context,
    category: Optional[str] = Field(None, description="The category to filter by (e.g., 'AI', 'Tech'). If omitted, all feeds will be returned."),
    ) -> str: # pragma: no cover
    """
    Returns the RSS feeds for various categories.
    The AI can use these URLs with the fetch_rss_feed tool.
    """
    output = await _get_feeds(ctx, category)
    return output

@mcp.tool()
async def fetch_rss_feed(
    url: str = Field(..., description="The valid RSS/Atom feed URL (must start with http/https)"),
    max_results: int = Field(default=5, ge=1, le=10, description="Number of articles to fetch. If the user asks for a specific number of items, use that value. Otherwise, use this limit to save bandwidth."),
    ctx: Context = None
    ) -> str: # pragma: no cover
    """
    Read an RSS feed from a URL and return the titles and links of the latest articles.
    Useful for getting news updates or content from blogs.
    """
    try:
        TypeAdapter(HttpUrl).validate_python(url)
    except Exception:
        if ctx: await ctx.error(f"Invalid URL: {url}")
        return "Error: Invalid URL. Please provide a valid web link starting with http:// or https://"
    
    try:
        logger.info(f"Accessing feed: {url}")    
        return await _fetch_rss_feed(url, max_results, ctx)

    except Exception as e:
        logger.error(f"Parsing error: {e}")
        if ctx: await ctx.error(f"Parsing error: {url}")
        return f"Error while getting the feed: {str(e)}"

def main(): # pragma: no cover
    import asyncio
    
    try:
        logging.info("Initializing database...")
        asyncio.run(init_db())
        
        logging.info("Starting the MCP server")
        mcp.run()
    except Exception as e:
        logging.error(f"Failed to start MCP server: {e}")
        
# --- STARTING ---
if __name__ == "__main__":main() # pragma: no cover

