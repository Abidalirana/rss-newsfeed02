import os
import sys
import asyncio
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collectoragent import fetch_all_rss, FeedOut
from agents import set_tracing_disabled, OpenAIChatCompletionsModel

# === ENV ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()
set_tracing_disabled(True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

# === SUMMARIZER FUNCTION (All in one request) ===
async def summarize_all_at_once(items: List[FeedOut]) -> str:
    # Build one big text block
    news_block = ""
    for idx, item in enumerate(items, start=1):
        news_block += f"{idx}. {item.title}\n{item.summary}\n\n"

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
        max_tokens=2000,  # Bigger limit for all news
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

# === MAIN ===
async def main():
    print("\n📰 Fetching RSS feeds...")
    items = await fetch_all_rss(max_per=3)  # Change max_per if needed
    print(f"✅ Got {len(items)} items, sending ALL to summarizer in one request...\n")

    summaries = await summarize_all_at_once(items)

    print("\n📄 Summarized Results:\n")
    print(summaries)

if __name__ == "__main__":
    asyncio.run(main())
