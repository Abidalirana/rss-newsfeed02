import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import hashlib
import httpx
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column, Mapped
from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ARRAY,
)
from sqlalchemy import select

# --- DB setup ---
DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost/newsfeed"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    symbols: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=True)

# --- Helpers ---

def clean_html(text: str) -> str:
    return BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)[:320]

def parse_datetime(date_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None

# --- RSS Feeds ---

RSS_FEEDS = {
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "TheStreet": "https://www.thestreet.com/.rss/full/",
    "FXStreet": "https://www.fxstreet.com/rss/news",
    "CryptoNews": "https://cryptonews.com/news/feed/",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US",
    "Nasdaq": "https://www.nasdaq.com/feed/rssoutbound?category=Business",
    "Investopedia": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "The Block": "https://www.theblock.co/rss",
    "CryptoSlate": "https://cryptoslate.com/feed/",
    "Watcher.Guru": "https://watcher.guru/feed",
    "Finbold": "https://finbold.com/feed",
    "ZeroHedge": "https://www.zerohedge.com/fullrss.xml",
}

# --- Main fetching function ---

async def fetch_and_store(max_per: int = 3) -> List[NewsItem]:
    collected_items = []
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async with httpx.AsyncClient(timeout=15) as client, async_session() as session:
        tasks = [client.get(url, follow_redirects=True) for url in RSS_FEEDS.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (source, resp) in zip(RSS_FEEDS.keys(), responses):
            if isinstance(resp, Exception) or resp.status_code != 200:
                print(f"Failed to fetch {source}")
                continue

            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:max_per]:
                url = entry.link
                exists = await session.scalar(select(NewsItem.id).where(NewsItem.url == url))
                if exists:
                    continue

                published = None
                if hasattr(entry, "published"):
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except Exception:
                        published = None

                summary = clean_html(entry.get("summary", ""))

                item = NewsItem(
                    title=entry.title,
                    source=source,
                    published_at=published,
                    content=None,
                    summary=summary,
                    tags=[],
                    symbols=[],
                    url=url,
                    provider="rss"
                )
                session.add(item)
                collected_items.append(item)
            await session.commit()
    return collected_items

# --- Create tables function ---

async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Wrapper function for collector ---

async def run_collector(messages=None):
    # If you want, parse messages here to set max_per, for now fixed 3
    max_per = 3
    collected_items = await fetch_and_store(max_per=max_per)
    return collected_items

# --- Main function to test ---

async def main():
    await create_tables()
    print("Tables created")

    print("Starting collector...")
    items = await run_collector()
    print(f"Collected {len(items)} new news items.")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.title} - {item.url}")

if __name__ == "__main__":
    asyncio.run(main())