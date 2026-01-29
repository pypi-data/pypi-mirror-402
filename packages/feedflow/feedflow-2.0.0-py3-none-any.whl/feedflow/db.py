# db.py
import aiosqlite
import os
from platformdirs import user_data_dir
from pathlib import Path
from fastmcp import Context
try:
	from .utils import detect_actual_language
except (ImportError, ValueError):# pragma: no cover
    from utils import detect_actual_language# pragma: no cover

default_dir = Path(user_data_dir('feedflow', appauthor=False))
data_dir = Path(os.getenv("FEEDFLOW_DATA_DIR", default_dir))
data_dir.mkdir(parents=True, exist_ok=True)

DB_PATH = data_dir / "feedflow.db"

async def init_db():
    """
    Init database
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS feeds (
                    id INTEGER PRIMARY KEY, 
                    name TEXT,
                    url TEXT, 
                    category TEXT,
                    language TEXT
                )
            ''')
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON feeds(category)")
            await conn.commit()

    print(f"Database ready in: {DB_PATH}")

async def _get_categories(ctx: Context = None) -> list[str]:
    """Retrieves the unique list of categories from the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT category FROM feeds WHERE category IS NOT NULL") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def _add_feed(name: str, url: str, category: str, lang: str, ctx: Context = None) -> str:
    """
    Adds a new RSS feed to the Feed list persistently.
    Returns a success or error formatted string message.

    Args:
        name (str): The name of the feed.
        url (str): The URL of the feed.
        category (str): The category of the feed.
        lang (str): The language of the feed.

    Returns:
        str: A success or error formatted string message.
    """
    try:
        if ctx: await ctx.info(f"Processing new feed: {name}")
        
        # language detection
        language = lang if lang else detect_actual_language(name)
        language = language if language else "Unknown"
        
        if ctx: await ctx.report_progress(1, 3)
        
        # Use async with for connection management
        async with aiosqlite.connect(DB_PATH) as conn:
            if ctx: await ctx.info("Saving to database...")
            
            # Execute the insert asynchronously
            await conn.execute(
                "INSERT INTO feeds (name, url, category, language) VALUES (?, ?, ?, ?)", 
                (name, url, category, language)
            )
            
            if ctx: await ctx.report_progress(2, 3)
            
            # Commit changes to the database
            await conn.commit()
            
        if ctx: await ctx.report_progress(3, 3)
        
        return f"Successfully added '{name}' to the {category} category."
    
    except Exception as e:
        if ctx: await ctx.error(f"Failed to add feed: {str(e)}")
        return f"Error adding feed: {str(e)}"

async def _remove_feed(feed: str, ctx: Context = None) -> str:
    """
    Removes a feed from the database by matching either its URL or its Name.
    Returns True if a record was deleted, False otherwise.
    """
    try:
        if ctx: await ctx.report_progress(1, 2)
        async with aiosqlite.connect(DB_PATH) as db:
            if ctx: await ctx.info("Trying to remove the feed from the datbase...")
            query = "DELETE FROM feeds WHERE url = ? OR name = ?"
            async with db.execute(query, (feed, feed)) as cursor:
                await db.commit()
                if ctx: await ctx.report_progress(2, 2)
                return cursor.rowcount > 0
    except Exception as e:
        if ctx: await ctx.error(f"Removing feed error: {str(e)}")
        return False
    
async def _get_feeds(ctx: Context = None, category: str = None) -> str:
    """
    Returns a list of RSS feeds for various categories.
    
    Returns:
        A formatted string listing all feeds.
    """

    try:
        if ctx: await ctx.info("Connecting to database...")
        
        if category:
            query = "SELECT name, url FROM feeds WHERE category = ?"
            params = (category,)
        else:
            query = "SELECT name, url, category FROM feeds"
            params = ()       
        
        async with aiosqlite.connect(DB_PATH) as conn:
            if ctx: await ctx.report_progress(1, 5)
            
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
            
            if ctx: await ctx.report_progress(2, 5)

        if not rows:
            if category:
                return f"No feeds found in the '{category}' category."
            else:
             return "No feeds configured. Use the 'add_feed' tool to add some!" 

        output = "CURRENT FEEDS:\n"
        count = 0
        for row in rows:
            count += 1
            if category:
                output += f"- {row[0]}: {row[1]}\n" # name e url
            else:
                output += f"- [{row[2]}] {row[0]}: {row[1]}\n" # category, name e url
            if ctx: await ctx.report_progress(3 + (count/len(rows)), 5)
        
        if ctx: 
            await ctx.info(f"Collected {len(rows)} feed with success.")
            await ctx.report_progress(5, 5)
            
        return output

    except Exception as e:
        if ctx: await ctx.error(f"Database Error: {str(e)}")
        return f"Error while getting feeds: {e}"
