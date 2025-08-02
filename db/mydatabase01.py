from typing import AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, ARRAY
from urllib.parse import urlparse

# -------------------------
# DATABASE CONFIGURATION
# -------------------------
DATABASE_URL = "postgresql+asyncpg://postgres:admin123@localhost:5432/agents_tracking"
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# -------------------------
# BASE CLASS
# -------------------------
class Base(DeclarativeBase):
    pass

# -------------------------
# TABLE DEFINITIONS
# -------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)

class FeedItem(Base):
    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    link: Mapped[str] = mapped_column(Text)
    published: Mapped[str] = mapped_column(String(100))  # Can be changed to DateTime
    summary: Mapped[str] = mapped_column(Text)
    hash: Mapped[str] = mapped_column(String(128), unique=True)

class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime)
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String))
    symbols: Mapped[list[str]] = mapped_column(ARRAY(String))
    url: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(Text)

# -------------------------
# CREATE TABLES FUNCTION
# -------------------------
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully.")

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def _get_value(item, key: str):
    """Helper to extract value from object or .value dict."""
    if hasattr(item, key):
        return getattr(item, key)
    elif hasattr(item, "value") and isinstance(item.value, dict):
        return item.value.get(key)
    return None

def _is_valid_url(url: str) -> bool:
    """Checks if a URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

# -------------------------
# SAVE FUNCTIONS
# -------------------------
async def save_feed_items_to_db(feed_items: list):
    async with async_session() as session:
        for item in feed_items:
            title = _get_value(item, "title")
            link = _get_value(item, "link")
            published = _get_value(item, "published")
            summary = _get_value(item, "summary")
            hash_value = _get_value(item, "hash")

            if not _is_valid_url(link):
                print(f"⚠️ Skipping invalid URL: {link}")
                continue

            db_item = FeedItem(
                title=title,
                link=link,
                published=published,
                summary=summary,
                hash=hash_value,
            )
            session.add(db_item)
        await session.commit()
        print("📦 Feed items saved to DB!")

async def save_news_items_to_db(news_items: list):
    async with async_session() as session:
        for item in news_items:
            db_item = NewsItem(
                title=item.title,
                source=item.source,
                published_at=item.published_at,
                content=item.content,
                summary=item.summary,
                tags=item.tags,
                symbols=item.symbols,
                url=item.url,
                provider=item.provider,
            )
            session.add(db_item)
        await session.commit()
        print("📰 News items saved to DB!")
