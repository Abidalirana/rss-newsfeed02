import os
import sys
import json
import asyncio
import re
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column, Mapped
from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ARRAY,
    update,
    select
)
from datetime import datetime
from bs4 import BeautifulSoup

# --- Load env and set API keys ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

# --- DB Setup ---
DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost/newsfeed"
engine = create_async_engine(DATABASE_URL, echo=False)
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

# --- OpenAI / Gemini Client Setup ---
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# === Helper to clean HTML from summary ===
def clean_html(text: str) -> str:
    return BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)[:320]

# === Clean Gemini API response to extract JSON ===
def clean_gemini_response(text: str) -> str:
    # Remove ```json ... ``` fences if present
    pattern = r"```json\s*(\[\s*{.*}\s*\])\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    # fallback: remove any ``` or ```json fences anyway
    return text.strip().strip("```").strip()

# === Tagger function that calls Gemini model and updates DB ===
async def tag_news_items_and_update_db(items: List[NewsItem], db_session: AsyncSession) -> List[dict]:
    news_list_str = "\n\n".join(
        [f"{i+1}. Title: {item.title}\nSummary: {item.summary or ''}" for i, item in enumerate(items)]
    )

    prompt = f"""
You are a financial tagging assistant.
Respond ONLY with valid JSON — no explanations, no text outside JSON.

For each news item below (title + summary):
1. Extract any stock symbols (e.g., AAPL, TSLA, MSFT)
2. Extract relevant tags such as: earnings, macro, fed, AI, tech, energy, crypto, etc.
3. Output a JSON array where each element matches the order of the news items.

Example:
[
  {{"symbols": ["AAPL"], "tags": ["earnings", "AI"]}},
  {{"symbols": ["TSLA"], "tags": ["auto", "earnings"]}}
]

News items:
{news_list_str}
    """

    resp = await client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0
    )

    raw_content = ""
    try:
        raw_content = (
            resp.choices[0].message["content"]
            if isinstance(resp.choices[0].message, dict)
            else resp.choices[0].message.content
        )
    except Exception as e:
        print("❌ Could not read model output:", e)
        return []

    if not raw_content or not raw_content.strip():
        print("❌ Model returned no content.")
        return []

    # Clean response from backticks/code fences before parsing
    cleaned_content = clean_gemini_response(raw_content)

    try:
        tags_data = json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON:", e)
        print("Raw model output:", raw_content)
        return []

    results = []
    for item, tags in zip(items, tags_data):
        symbols = tags.get("symbols", [])
        tags_list = tags.get("tags", [])

        await db_session.execute(
            update(NewsItem)
            .where(NewsItem.id == item.id)
            .values(symbols=symbols, tags=tags_list)
        )

        results.append({
            "title": item.title,
            "summary": item.summary,
            "symbols": symbols,
            "tags": tags_list,
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None
        })

    return results

# === Fetch untagged news from DB ===
async def get_untagged_news(session: AsyncSession, limit: int = 10) -> List[NewsItem]:
    stmt = select(NewsItem).where(
        (NewsItem.tags == []) | (NewsItem.symbols == [])
    ).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

# === Main tagging loop ===
async def main_tagger():
    async with async_session() as session:
        untagged = await get_untagged_news(session)
        if not untagged:
            print("No untagged news items found.")
            return
        tagged = await tag_news_items_and_update_db(untagged, session)
        await session.commit()  # Commit after updates
        print(f"Tagged {len(tagged)} news items:")
        for item in tagged:
            print(item)

# === Create tables ===
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

# === Run everything ===
async def main():
    await create_tables()
    await main_tagger()

if __name__ == "__main__":
    asyncio.run(main())

#===============================================================================
# Wrapper to tag passed items (if you want to tag from code, e.g. pipeline step)
async def run_tagger(items: List[NewsItem]) -> List[dict]:
    async with async_session() as session:
        tagged_items = await tag_news_items_and_update_db(items, session)
        await session.commit()
        return tagged_items