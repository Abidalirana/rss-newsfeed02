from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column, Mapped
from sqlalchemy import String, Integer, Text, DateTime, ARRAY
from datetime import datetime

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
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    symbols: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=True)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy import select
import logging

import logging

# Configure logging to show only errors (no info/debug)
logging.basicConfig(
    level=logging.ERROR,  # Only errors and above get logged
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]  # Console output
)

async def save_feed_items_to_db(items: list[dict]):
    try:
        async with async_session() as session:
            async with session.begin():
                urls = [item['url'] for item in items]
                if not urls:
                    return

                result = await session.execute(
                    select(NewsItem.url).where(NewsItem.url.in_(urls))
                )
                existing_urls = set(row[0] for row in result.fetchall())

                for item in items:
                    if item['url'] in existing_urls:
                        continue
                    news_item = NewsItem(
                        title=item.get('title', 'No Title'),
                        source=item.get('source'),
                        published_at=parse_datetime(item.get('published_at')),
                        content=item.get('content'),
                        summary=item.get('summary'),
                        tags=item.get('tags', []),
                        symbols=item.get('symbols', []),
                        url=item['url'],
                        provider=item.get('provider')
                    )
                    session.add(news_item)
            await session.commit()
    except Exception as e:
        logging.error(f"Failed to save feed items: {e}")

def parse_datetime(dt):
    # Converts string to datetime if needed, or returns None
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return None
