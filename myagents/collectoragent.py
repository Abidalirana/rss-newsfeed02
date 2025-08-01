# myagents/collectoragent.py
import os
import sys
import asyncio

# Ensure parent dir is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel
from myagents.mytools import fetch_rss, filter_new, scrape_and_compress  # ✅ Only required tools

# === ENV & Config ===
load_dotenv()
set_tracing_disabled(True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

# === External Model Setup ===
external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# === Agent Setup ===
collector = Agent(
    name="CollectorAgent",
    instructions="""
You're a News Collection Agent.

1. Use `fetch_rss` to get new RSS articles.
2. Use `filter_new` to skip already-seen titles.
3. Use `scrape_and_compress` to extract and shorten the content.
Return title, url, published_at, excerpt.
""",
    tools=[fetch_rss, filter_new, scrape_and_compress],
    model=model
)

# === Runner ===
if __name__ == "__main__":
    async def main():
        print("📰 Collector Agent Running...")
        result = await Runner.run(collector, [{"role": "user", "content": "Collect latest financial news."}])
        print("\n📢 Collected Output:\n")
        print(result.final_output)

    asyncio.run(main())
