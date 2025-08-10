import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from typing import List
# import httpx  # Commented out since we won't do HTTP requests
from sqlalchemy import update, select, and_
from sqlalchemy.ext.asyncio import AsyncSession


from myagents.db import async_session, NewsItem
from myagents.taggeragent import run_tagger  

logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
# logging.getLogger("httpx").setLevel(logging.ERROR)  # No httpx calls, so comment this

# FUNDEDFLOW_API_URL = os.getenv("FUNDEDFLOW_API_URL")
# FUNDEDFLOW_API_KEY = os.getenv("FUNDEDFLOW_API_KEY")

async def get_unpublished_news(session: AsyncSession, limit: int = 10) -> List[NewsItem]:
    stmt = select(NewsItem).where(
        and_(
            NewsItem.publisher.is_(False),
            NewsItem.url.isnot(None),
            NewsItem.url != '',
            NewsItem.url != 'None'
        )
    ).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def publish_to_fundedflow(item: NewsItem) -> bool:
    # Since publishing is disabled, just pretend it's successful if URL valid
    if not item.url or not isinstance(item.url, str) or item.url.strip() == "" or item.url.strip().lower() == "none":
        logging.error(f"Skipping '{item.title}': missing or invalid URL.")
        return False
    
    # Just log the item instead of sending it
    print(f"Would publish: {item.title} | URL: {item.url}")
    return True

async def run_publisher(limit: int = 10) -> int:
    published_count = 0
    try:
        async with async_session() as session:
            unpublished = await get_unpublished_news(session, limit=limit)
            if not unpublished:
                print("No unpublished news found.")
                return 0

            for item in unpublished:
                success = await publish_to_fundedflow(item)
                if success:
                    await session.execute(
                        update(NewsItem)
                        .where(NewsItem.id == item.id)
                        .values(publisher=True)
                    )
                    published_count += 1
            await session.commit()
    except Exception as e:
        logging.error(f"Unexpected error in publisher: {e}")
        return 0

    if published_count == 0:
        print("No news items were published.")
    else:
        print(f"Marked {published_count} news item{'s' if published_count > 1 else ''} as published.")

    return published_count


# Wrapper function added here as requested
async def run_publisher_wrapper(limit: int = 10) -> int:
    """
    Wrapper function for run_publisher.
    Calls run_publisher and returns the published count.
    """
    count = await run_publisher(limit=limit)
    return count


if __name__ == "__main__":
    asyncio.run(run_publisher())
