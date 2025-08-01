# myagents/summarizeragent.py

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel
from myagents.mytools import FeedOut  # ✅ follow mytools.py structure

# === Load env ===
load_dotenv()
set_tracing_disabled(True)

# === External Gemini model ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# === Agent ===
summarizer = Agent(
    name="SummarizerAgent",
    instructions="""
        Summarize the excerpt into ≤3 bullet points (≤120 characters each).
        Extract relevant stock symbols (e.g., AAPL, TSLA).
        Tag the article with topics: earnings, macro, analyst_rating, etc.
        Respond in strict JSON format using the FeedOut schema.
    """,
    model=model,
    output_type=FeedOut,  # ✅ Using FeedOut from mytools.py
)

# === Runner ===
async def run_summarizer(items: list[dict]) -> list[FeedOut]:
    runner = Runner(agent=summarizer)
    return await runner.run(items)
