#summarzie rgood wrong 


import os
import sys
import asyncio
import json
from typing import List, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collectoragent import fetch_all_rss, FeedOut
from agents import set_tracing_disabled, OpenAIChatCompletionsModel
from pydantic import BaseModel, ValidationError


# === ENV SETUP ===
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


# === Pydantic model for structured summary ===
class SummaryItem(BaseModel):
    title: str
    summary: List[str]
    symbols: Optional[List[str]] = []
    tags: Optional[List[str]] = []


# === Helper function to clean GPT JSON output ===
def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()


    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end+1]
    return text


# === Parse cleaned JSON string to list of SummaryItem ===
def parse_json_summaries(text: str) -> List[SummaryItem]:
    cleaned = clean_json_text(text)
    try:
        data = json.loads(cleaned)
        summaries = [SummaryItem(**item) for item in data]
        return summaries
    except (json.JSONDecodeError, ValidationError) as e:
        print("❌ Failed to parse JSON summaries:", e)
        print("Raw response was:\n", text)
        return []


# === Summarizer function making one GPT call ===
async def summarize_all_at_once(items: List[FeedOut]) -> List[SummaryItem]:
    news_block = ""
    for idx, item in enumerate(items, start=1):
        news_block += f"{idx}. {item.title}\n{item.summary}\n\n"


    prompt = f"""
You are a financial news summarizer.


Here are multiple news articles from RSS feeds:


{news_block}


Task:
1. Summarize each news item into up to 3 bullet points (max 120 characters each).
2. Output a JSON array of objects with fields:
   - title: original article title (string)
   - summary: list of bullet points (array of strings)
   - symbols: list of stock symbols (array of strings, can be empty)
   - tags: list of relevant tags (array of strings, can be empty)


Respond ONLY with valid JSON, no extra text.
"""


    resp = await client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.2
    )
    text_response = resp.choices[0].message.content.strip()
    return parse_json_summaries(text_response)


# === Main CLI test runner ===
async def main():
    print("\n📰 Fetching RSS feeds...")
    items = await fetch_all_rss(max_per=3)  # Adjust max_per as needed
    print(f"✅ Got {len(items)} items, sending all to summarizer in one request...\n")


    summaries = await summarize_all_at_once(items)


    print("\n📄 Summarized Results:\n")
    for item in summaries:
        print(f"Title: {item.title}")
        for bullet in item.summary:
            print(f" • {bullet}")
        print(f"Symbols: {', '.join(item.symbols) if item.symbols else 'None'}")
        print(f"Tags: {', '.join(item.tags) if item.tags else 'None'}")
        print()


if __name__ == "__main__":
    asyncio.run(main())




