# agents/taggeragent.py


import os
import sys
sys.path.append("./")
import asyncio

from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, function_tool, Runner, OpenAIChatCompletionsModel

# ========= Load environment ========= #
load_dotenv()

# ========= Gemini Client Setup ========= #
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-pro",
    openai_client=external_client
)

# ========= Schemas ========= #
class NewsItemInput(BaseModel):
    title: str
    summary: str

class TaggedNews(BaseModel):
    symbols: List[str]
    tags: List[str]

# ========= Agent ========= #
tagger_agent = Agent(
    name="TaggerAgent",
    model=model,
    instructions="""
You are a financial tagging assistant.

Given a news `title` and `summary`, extract:
1. Any stock **symbols** (e.g., AAPL, TSLA, MSFT)
2. Relevant **tags** such as: 'earnings', 'macro', 'fed', 'AI', 'tech', 'energy', etc.

Only return symbols clearly mentioned or implied (e.g., Apple → AAPL).
Respond only with a clean, structured JSON like:
{
  "symbols": ["AAPL"],
  "tags": ["earnings", "AI"]
}
"""
)

# ========= Test Function ========= #
async def test_tagger():
    news = NewsItemInput(
        title="Apple beats Q2 earnings expectations with strong iPhone sales",
        summary="Apple Inc. reported better-than-expected Q2 earnings due to a surge in iPhone demand, sending AAPL shares higher."
    )
    messages = [{"role": "user", "content": f"Title: {news.title}\n\nSummary: {news.summary}"}]
    result = await Runner.run(tagger_agent, messages)
    print("⏹ Final output:")
    print(result.final_output)

# ========= Async Runner ========= #
if __name__ == "__main__":
    asyncio.run(test_tagger())
