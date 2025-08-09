import sys
import os
import traceback
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from myagents.collectoragent import run_collector
from myagents.summarizeragent import run_summarizer
from myagents.taggeragnet import run_tagger   
from myagents.db import save_feed_items_to_db

class FeedInputConverter:
    @staticmethod
    def to_messages(input_data):
        # just return input data as messages for now
        return input_data

async def run_pipeline():
    try:
        input_data = [
            {
                "symbols": ["AAPL", "TSLA"],
                "max_results": 5,
                "filters": None
            }
        ]
        messages = FeedInputConverter.to_messages(input_data)
        collected = await run_collector(messages)
        summarized = await run_summarizer(collected)
        tagged = await run_tagger(summarized)
        await save_feed_items_to_db(tagged)
        print(f"Pipeline finished: {len(tagged)} items saved.")
    except Exception as e:
        print(f"Pipeline error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_pipeline())
