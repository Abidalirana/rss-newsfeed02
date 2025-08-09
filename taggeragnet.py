import os
import sys
import json
import asyncio
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Make sure we can import from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from collectoragent import FeedOut  # Same FeedOut used by summarizer
from agents import set_tracing_disabled, OpenAIChatCompletionsModel

# === ENV ===
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

# === TAGGER FUNCTION (BATCH) ===
async def tag_news_items(items: List[FeedOut]) -> List[dict]:
    """
    Tag all summarized items in one API call.
    Returns list of dicts: {title, summary, symbols, tags, link, published}
    """
    news_list_str = "\n\n".join(
        [f"{i+1}. Title: {item.title}\nSummary: {item.summary}" for i, item in enumerate(items)]
    )

    prompt = f"""
You are a financial tagging assistant.
Respond ONLY with valid JSON — no explanations, no text outside JSON.

For each news item below (title + summary):
1. Extract any stock **symbols** (e.g., AAPL, TSLA, MSFT)
2. Extract relevant **tags** such as: earnings, macro, fed, AI, tech, energy, crypto, etc.
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

    # --- Safe extraction ---
    raw_content = ""
    try:
        raw_content = (
            resp.choices[0].message["content"]
            if isinstance(resp.choices[0].message, dict)
            else resp.choices[0].message.content
        )
    except Exception as e:
        print("❌ Could not read model output:", e)

    if not raw_content or not raw_content.strip():
        print("❌ Model returned no content. Full response:")
        print(resp)
        return []

    # --- Safe JSON parsing ---
    try:
        tags_data = json.loads(raw_content.strip())
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON:", e)
        print("🔍 Raw model output:")
        print(raw_content)
        return []

    # --- Combine with input items ---
    final = []
    for item, tags in zip(items, tags_data):
        final.append({
            "title": item.title,
            "summary": item.summary,
            "symbols": tags.get("symbols", []),
            "tags": tags.get("tags", []),
            "link": item.link,
            "published": item.published
        })

    return final

# === DEMO ===
async def demo():
    sample_items = [
        FeedOut(
            title="Apple beats Q2 earnings expectations with strong iPhone sales",
            summary="Apple Inc. reported better-than-expected Q2 earnings due to strong iPhone demand, sending AAPL shares higher.",
            link="https://example.com/apple-earnings",
            published="2025-08-09T10:00:00Z",
            hash="abc123"
        ),
        FeedOut(
            title="Tesla launches new EV model aimed at budget-conscious buyers",
            summary="Tesla unveiled a lower-priced electric vehicle to capture a broader market segment. Analysts expect TSLA sales to grow.",
            link="https://example.com/tesla-ev",
            published="2025-08-09T11:00:00Z",
            hash="def456"
        )
    ]

    tagged = await tag_news_items(sample_items)
    print("🏷️ Tagged Results:")
    for t in tagged:
        print(t)

if __name__ == "__main__":
    asyncio.run(demo())
