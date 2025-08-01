# --- main.py ---
import asyncio
from myagents.collectoragent import collector
from myagents.summarizeragent import run_summarizer
from myagents.taggeragnet import tagger_agent
from myagents.mainagent import main_agent

from agents import Runner

# Main async function to be called from scheduler
async def main():
    test_messages = [{
        "role": "user",
        "content": "Fetch news for: openai, chatgpt\nMax results: 2\nFilters: None"
    }]

    print("🔁 Running main() from main.py...")
    result = await Runner.run(main_agent, input=test_messages)
    print("✅ Final Output:\n", result.final_output)

# Optional: Direct run if main.py is executed alone
if __name__ == "__main__":
    asyncio.run(main())
