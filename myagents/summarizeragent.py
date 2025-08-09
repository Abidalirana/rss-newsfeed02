import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import re
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
#from collectoragent import NewsItem, Base  # Your ORM model
from myagents.collectoragent import NewsItem, Base

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_tracing_disabled, OpenAIChatCompletionsModel

# === ENV & DB setup ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()
set_tracing_disabled(True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost/newsfeed"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === Fetch news without summaries from DB ===
async def fetch_unsummarized_news(max_items: int = 10) -> List[NewsItem]:
    async with async_session() as session:
        result = await session.execute(
            select(NewsItem).where((NewsItem.summary == None) | (NewsItem.summary == '')).limit(max_items)
        )
        return result.scalars().all()

# === Summarizer function ===
async def summarize_all_at_once(items: List[NewsItem]) -> str:
    news_block = ""
    for idx, item in enumerate(items, start=1):
        news_block += f"{idx}. {item.title}\n{item.summary or ''}\n\n"

    prompt = f"""
You are a financial news summarizer.

Here are multiple news articles from RSS feeds:

{news_block}

Task:
1. Summarize each news item into ≤3 bullet points (≤120 chars each).
2. Keep bullet points short & factual.
3. For each news item, keep its original number.

Output format:
<number>. <original title>
   • bullet1
   • bullet2
   • bullet3
"""

    resp = await client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

# === Parse AI response and update DB summaries ===
async def update_summaries(items: List[NewsItem], summaries_text: str):
    pattern = re.compile(r'(\d+)\.\s.*?\n((?:\s*•.*\n?)+)', re.MULTILINE)
    matches = pattern.findall(summaries_text)

    summary_map = {}
    for number, bullets in matches:
        bullet_points = "\n".join(bullets.strip().splitlines())
        summary_map[int(number)] = bullet_points

    async with async_session() as session:
        for idx, item in enumerate(items, start=1):
            if idx in summary_map:
                item.summary = summary_map[idx]
                session.add(item)
        await session.commit()

# === Wrapper for summarizer, accepts list of NewsItem and returns updated items ===
async def run_summarizer(items: List[NewsItem]) -> List[NewsItem]:
    if not items:
        return []

    summaries_text = await summarize_all_at_once(items)
    await update_summaries(items, summaries_text)
    return items

# === Main ===
async def main():
    print("\n📥 Fetching unsummarized news from DB...")
    items = await fetch_unsummarized_news(max_items=10)
    if not items:
        print("No news to summarize.")
        return

    print(f"📰 Summarizing {len(items)} news items...")
    summaries_text = await summarize_all_at_once(items)
    print("\n📄 Summarizer output:\n", summaries_text)

    print("\n💾 Updating summaries in DB...")
    await update_summaries(items, summaries_text)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())