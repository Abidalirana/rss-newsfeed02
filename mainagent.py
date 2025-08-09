import os
import sys
import asyncio
import aiohttp
import re
from typing import List, Any
from dotenv import load_dotenv

# Add project root for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env variables
load_dotenv()

# Configs
API_ENDPOINT = os.getenv("FUNDEDFLOW_API")
API_KEY = os.getenv("FUNDEDFLOW_API_KEY")

# Import your agents
from myagents.collectoragent import fetch_all_rss, FeedOut
from myagents.summarizeragent import summarize_all_at_once
from myagents.taggeragnet import tag_news_items

# Import your model setup (OpenAI client)
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

# Setup OpenAI Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env file!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === Pipeline Steps ===

async def collect_news(max_results: int = 5) -> List[Any]:
    print("🚀 Collecting news...")
    items = await fetch_all_rss()
    print(f"✅ Collected {len(items)} items")
    return items

async def summarize_news(items: List[Any]) -> List[FeedOut]:
    print("📝 Summarizing news...")
    summarized_text = await summarize_all_at_once(items)  # This returns a big string

    # Parse the summarized_text back into list of FeedOut objects
    summarized_items = []
    # Split by pattern like: "1. Title\n • bullet1\n • bullet2\n\n2. Title2..."
    parts = re.split(r'\n\d+\.\s', "\n" + summarized_text)  # Add leading \n to capture first split properly

    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n')
        title = lines[0].strip()
        # Join bullet points into one summary string
        summary = " ".join(line.strip(" •") for line in lines[1:] if line.startswith("•"))
        summarized_items.append(
            FeedOut(
                title=title,
                summary=summary,
                link="",       # Optionally you can map original links if needed
                published="",
                hash=""
            )
        )

    print(f"✅ Parsed summarized into {len(summarized_items)} items")
    return summarized_items

async def tag_news(items: List[Any]) -> List[Any]:
    print("🏷 Tagging news...")
    tagged = await tag_news_items(items)
    print(f"✅ Tagged {len(tagged)} items")
    return tagged

async def publish_one(session: aiohttp.ClientSession, news: dict):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        async with session.post(API_ENDPOINT, json=news, headers=headers) as resp:
            if resp.status == 200:
                print(f"✅ Published: {news.get('title', 'No Title')}")
            else:
                print(f"❌ Failed to publish: {news.get('title', 'No Title')} (Status: {resp.status})")
    except Exception as e:
        print(f"❌ Exception publishing {news.get('title', 'No Title')}: {e}")

async def publish_news(news_items: List[dict]):
    print("📢 Publishing to FundedFlow...")
    async with aiohttp.ClientSession() as session:
        tasks = [publish_one(session, news) for news in news_items]
        await asyncio.gather(*tasks)
    print("✅ Publishing completed.")

# --- Main Pipeline Runner ---

async def main(max_results: int = 5):
    collected = await collect_news(max_results)
    summarized = await summarize_news(collected)
    tagged = await tag_news(summarized)

    publish_items = []
    for item in tagged:
        publish_items.append({
            "title": getattr(item, "title", ""),
            "link": getattr(item, "link", ""),
            "summary": getattr(item, "summary", ""),
            "tags": getattr(item, "tags", []),
            "published_at": getattr(item, "published", ""),
        })

    await publish_news(publish_items)

if __name__ == "__main__":
    asyncio.run(main())
