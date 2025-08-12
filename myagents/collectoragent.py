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
    select
)

# 🆕 Added import for newspaper3k
from newspaper import Article

# --- DB setup ---
#DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost/newsfeed"
# --- DB setup ---
import os
from dotenv import load_dotenv

load_dotenv()  # load .env in local dev, ignored in production on Render
DATABASE_URL = os.environ["DATABASE_URL"]


# 🚫 Changed echo=True → echo=False to stop printing every SQL query
engine = create_async_engine(DATABASE_URL, echo=False)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)  # 🆗 Will store full article text here
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    symbols: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=True)

# --- Helpers ---
def clean_html(text: str) -> str:
    """Remove HTML tags and limit to 320 chars."""
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
    # Trading idea & analysis focused feeds:
    "TradingView": "https://www.tradingview.com/feed.xml",
    "Investing.com": "https://www.investing.com/rss/news_25.rss",
    "StockTwits": "https://stocktwits.com/streams/trending.rss",
    "ForexFactory": "https://www.forexfactory.com/ffcal_week_this.xml",
    "DailyFX": "https://www.dailyfx.com/feeds/market-news.xml",
    "Benzinga": "https://www.benzinga.com/rss/markets-news",
}

# --- Main fetching function for RSS ---
async def fetch_and_store(max_per: int = 3) -> List[NewsItem]:
    """
    Fetch articles from RSS feeds, extract full content using newspaper3k, and store in DB.
    """
    collected_items = []
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async with httpx.AsyncClient(timeout=15) as client, async_session() as session:
        tasks = [client.get(url, follow_redirects=True) for url in RSS_FEEDS.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (source, resp) in zip(RSS_FEEDS.keys(), responses):
            if isinstance(resp, Exception) or resp.status_code != 200:
                # 🚫 Removed verbose print — was: print(f"Failed to fetch {source}")
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

                # 🆕 Use newspaper3k to get full article text
                try:
                    article_obj = Article(url)
                    article_obj.download()
                    article_obj.parse()
                    full_text = article_obj.text
                except Exception:
                    # 🚫 Removed error printing for failed parsing
                    full_text = None

                item = NewsItem(
                    title=entry.title,
                    source=source,
                    published_at=published,
                    content=full_text,  # 🆕 store full text
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

# --- Custom TradingView HTML scraper ---
async def fetch_tradingview_news() -> List[NewsItem]:
    """
    Fetch news from TradingView and extract full article text using newspaper3k.
    """
    url = "https://www.tradingview.com/news-flow"
    collected_items = []

    async with httpx.AsyncClient(timeout=15) as client, async_session() as session:
        resp = await client.get(url)
        if resp.status_code != 200:
            # 🚫 Removed: print("Failed to fetch TradingView news")
            return collected_items

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Example selector: adjust as needed if TradingView changes HTML
        articles = soup.select("div.tv-feed__item")
        
        for article in articles:
            title_tag = article.select_one("a.tv-feed__item__title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            news_url = "https://www.tradingview.com" + title_tag["href"]

            exists = await session.scalar(select(NewsItem.id).where(NewsItem.url == news_url))
            if exists:
                continue

            # 🆕 Use newspaper3k to fetch full text
            try:
                article_obj = Article(news_url)
                article_obj.download()
                article_obj.parse()
                full_text = article_obj.text
            except Exception:
                # 🚫 Removed printing of parsing errors
                full_text = None

            item = NewsItem(
                title=title,
                source="TradingView",
                published_at=None,
                content=full_text,  # 🆕 store full text
                summary=None,
                tags=[],
                symbols=[],
                url=news_url,
                provider="html-scraper"
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
    max_per = 3
    rss_items = await fetch_and_store(max_per=max_per)
    tradingview_items = await fetch_tradingview_news()
    return rss_items + tradingview_items

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
