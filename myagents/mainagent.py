# --- mainagent.py ---
import sys
import os
import asyncio
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents import (
    Agent, handoff, HandoffInputData, Runner,
    set_tracing_disabled, OpenAIChatCompletionsModel
)
from agents.extensions import handoff_filters

from myagents.mytools import (
    fetch_rss, filter_new, scrape_and_compress,
    summarize_text, tag_topics, FeedOut
)
from myagents.collectoragent import collector
from myagents.summarizeragent import summarizer
from myagents.taggeragnet import tagger_agent
from agents import function_tool

# ✅ Input model for Feed
class FeedInput(BaseModel):
    symbols: List[str]
    max_results: int
    filters: List[str] | None = None

# ✅ Input converter: converts FeedInput to messages
class FeedInputConverter:
    @staticmethod
    def to_messages(inputs: List[FeedInput]) -> List[dict]:
        messages = []
        for inp in inputs:
            msg = (
                f"Fetch news for: {', '.join(inp.symbols)}\n"
                f"Max results: {inp.max_results}\n"
                f"Filters: {', '.join(inp.filters) if inp.filters else 'None'}"
            )
            messages.append({"role": "user", "content": msg})
        return messages

# ✅ Optional: input filter before summarization
def to_summarizer_filter(h: HandoffInputData) -> HandoffInputData:
    h = handoff_filters.remove_all_tools(h)
    return HandoffInputData(
        input_history=h.input_history[-1:],
        pre_handoff_items=(),
        new_items=h.new_items,
    )

# ✅ Load env + Gemini setup
load_dotenv()
set_tracing_disabled(True)

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

# ✅ Main agent definition
main_agent = Agent(
    name="MainAgent",
    model=model,
    instructions="""
Step 1: Handoff to CollectorAgent.
Step 2: Handoff collected items to SummarizerAgent.
Step 3: Handoff to TaggerAgent.
Return final FeedOut.
""",
    handoffs=[
        handoff(collector),
        handoff(summarizer, input_filter=to_summarizer_filter),
        handoff(tagger_agent),
    ],
    tools=[
        fetch_rss,
        filter_new,
        scrape_and_compress,
        summarize_text,
        tag_topics
    ]
)

# ✅ Runner and test input
async def run_main_agent_test():
    test_input = [FeedInput(
        symbols=["openai", "chatgpt"],
        max_results=2,
        filters=None
    )]

    # Convert FeedInput to messages BEFORE passing into Runner
    messages = FeedInputConverter.to_messages(test_input)

    result = await Runner.run(
        main_agent,
        input=messages
    )

    print("✅ Final Output from MainAgent:\n", result.final_output)



if __name__ == "__main__":
    asyncio.run(run_main_agent_test())
