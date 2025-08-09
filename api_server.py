# api_server.py
import os
import sys
import re
from fastapi import FastAPI, HTTPException
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from myagents.db import async_session, NewsItem  
from openai import AsyncOpenAI
from dotenv import load_dotenv

app = FastAPI()

# Load env (no tracing disabling needed)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in environment")

# Setup OpenAI client for Gemini (use client directly)
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def serialize_news(news: NewsItem):
    return {
        "id": news.id,
        "title": news.title,
        "source": news.source,
        "published_at": news.published_at.isoformat() if news.published_at else None,
        "content": news.content,
        "summary": news.summary,
        "tags": news.tags,
        "symbols": news.symbols,
        "url": news.url,
        "provider": news.provider
    }

@app.get("/")
def home():
    return {"message": "Agent API is running!"}

@app.get("/news")
async def list_news():
    async with async_session() as session:
        result = await session.execute(select(NewsItem))
        news_list = result.scalars().all()
        return [serialize_news(n) for n in news_list]

@app.get("/news/{news_id}")
async def get_news(news_id: int):
    async with async_session() as session:
        result = await session.execute(select(NewsItem).where(NewsItem.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        return serialize_news(news)

@app.post("/news")
async def create_news(news_item: dict):
    async with async_session() as session:
        new_news = NewsItem(**news_item)
        session.add(new_news)
        try:
            await session.commit()
            await session.refresh(new_news)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="News with this URL already exists")
        return serialize_news(new_news)

@app.patch("/news/{news_id}")
async def update_news(news_id: int, updates: dict):
    async with async_session() as session:
        result = await session.execute(select(NewsItem).where(NewsItem.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        for key, value in updates.items():
            if hasattr(news, key):
                setattr(news, key, value)
        await session.commit()
        await session.refresh(news)
        return serialize_news(news)

@app.delete("/news/{news_id}")
async def delete_news(news_id: int):
    async with async_session() as session:
        result = await session.execute(select(NewsItem).where(NewsItem.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        await session.delete(news)
        await session.commit()
        return {"message": "Deleted successfully"}

# === Summarizer functions ===

async def fetch_unsummarized_news(max_items: int = 10):
    async with async_session() as session:
        result = await session.execute(
            select(NewsItem).where((NewsItem.summary == None) | (NewsItem.summary == '')).limit(max_items)
        )
        return result.scalars().all()

async def summarize_all_at_once(items):
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

async def update_summaries(items, summaries_text):
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

@app.post("/run-agent")
async def run_agent():
    items = await fetch_unsummarized_news(max_items=10)
    if not items:
        return {"message": "No news to summarize."}
    summaries_text = await summarize_all_at_once(items)
    await update_summaries(items, summaries_text)
    return {"message": f"Summarized {len(items)} news items."}
