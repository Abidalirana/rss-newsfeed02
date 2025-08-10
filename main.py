# main.py (your controller)

from myagents.collectoragent import run_collector
from myagents.summarizeragent import run_summarizer
from myagents.taggeragent import run_tagger
from myagents.publisheragent import run_publisher 

async def run_pipeline():
    collected = await run_collector()
    summarized = await run_summarizer(collected)
    tagged = await run_tagger(summarized)
    published_count = await run_publisher()  # run publisher after tagger
    print(f"Pipeline finished: {len(tagged)} items saved, {published_count} items published.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_pipeline())
