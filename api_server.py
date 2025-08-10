# api_server.py
import os
from fastapi import FastAPI, HTTPException
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from myagents.db import async_session, NewsItem
from dotenv import load_dotenv

app = FastAPI()

# Load env variables
load_dotenv()

# === Serializer ===
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
        "provider": news.provider,
        "publisher": news.publisher  # Added publisher field
    }

# === Basic Routes ===
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

# === Agent Endpoints ===
@app.post("/run-collector")
async def run_collector_endpoint():
    from myagents.collectoragent import run_collector
    count = await run_collector()
    return {"message": f"Collected {count} news items."}

@app.post("/run-summarizer")
async def run_summarizer_endpoint():
    from myagents.summarizeragent import run_agent
    count = await run_agent()
    return {"message": f"Summarized {count} news items."}

@app.post("/run-tagger")
async def run_tagger_endpoint():
    from myagents.taggeragent import run_tagger
    count = await run_tagger()
    return {"message": f"Tagged {count} news items."}

@app.post("/run-publisher")
async def run_publisher_endpoint():
    from myagents.publisheragent import run_publisher
    count = await run_publisher()
    return {"message": f"Published {count} news items."}

@app.post("/run-pipeline")
async def run_pipeline_endpoint():
    from myagents.collectoragent import run_collector
    from myagents.summarizeragent import run_agent
    from myagents.taggeragent import run_tagger
    from myagents.publisheragent import run_publisher

    collected = await run_collector()
    summarized = await run_agent()
    tagged = await run_tagger()
    published = await run_publisher()

    return {
        "message": "Pipeline complete",
        "collected": collected,
        "summarized": summarized,
        "tagged": tagged,
        "published": published
    }



#uvicorn api_server:app --reload




