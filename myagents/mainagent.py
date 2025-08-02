# --- mainagent.py ---
import sys
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- AGENT PLATFORM IMPORTS ---
from agents import (
    Agent, handoff, HandoffInputData, Runner,
    set_tracing_disabled, OpenAIChatCompletionsModel
)
from agents.extensions import handoff_filters

# --- AGENT COMPONENTS ---
from myagents.mytools import (
    fetch_rss, filter_new, scrape_and_compress,
    summarize_text, tag_topics, FeedOut
)
from myagents.collectoragent import collector
from myagents.summarizeragent import summarizer
from myagents.taggeragnet import tagger_agent

# --- DATABASE ---
from db.mydatabase01 import save_feed_items_to_db

# ✅ Result wrapper
@dataclass
class AgentResult:
    final_output: str
    new_items: List[Any]  # MessageOutputItem or dict
    metadata: Optional[Dict[str, Any]] = None

# ✅ Feed input model
class FeedInput(BaseModel):
    symbols: List[str]
    max_results: int
    filters: List[str] | None = None

# ✅ Converts FeedInput to messages
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

# ✅ Filter before summarizer agent
def to_summarizer_filter(h: HandoffInputData) -> HandoffInputData:
    h = handoff_filters.remove_all_tools(h)
    return HandoffInputData(
        input_history=h.input_history[-1:],
        pre_handoff_items=(),
        new_items=h.new_items,
    )

# ✅ Load environment variables
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

# ✅ Main Agent
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

# ✅ Runner
async def run_main_agent_test():
    test_input = [FeedInput(
        symbols=["openai", "chatgpt"],
        max_results=2,
        filters=None
    )]

    messages = FeedInputConverter.to_messages(test_input)
    result = await Runner.run(main_agent, input=messages)

    # Filter valid items (fix: no `.get()`)
    valid_items = [
        item for item in result.new_items
        if hasattr(item, "link") and hasattr(item, "title") and item.link and item.title
    ]

    metadata = {
        "agent": "MainAgent",
        "items_collected": len(valid_items),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    custom_result = AgentResult(
        final_output=result.final_output,
        new_items=valid_items,
        metadata=metadata
    )

    # Print result
    print("\n✅ Final Output from MainAgent:\n")
    print(custom_result.final_output)

    print("\n📊 Metadata:", metadata)

    if valid_items:
        print(f"\n🧾 Valid Feed Items ({len(valid_items)}):")
        for i, item in enumerate(valid_items, 1):
            print(f"\n{i}. 📰 {item.title}")
            print(f"🔗 {item.link}")
            print(f"📅 {getattr(item, 'published', 'N/A')}")
            print(f"📄 {getattr(item, 'summary', 'No summary')}")
            print("-" * 40)

        # Save to DB
        await save_feed_items_to_db(valid_items)
        print(f"\n💾 {len(valid_items)} valid items saved to DB.")
    else:
        print("\n⚠️ No valid items to save.")
# ✅ Export for external use
run_main_agent = run_main_agent_test
# ✅ Entry point
if __name__ == "__main__":
   
    asyncio.run(run_main_agent_test())
   

