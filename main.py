import asyncio
from myagents.collectoragent import run_collector
from myagents.summarizeragent import run_summarizer
from myagents.taggeragent import run_tagger
from myagents.mainagent import run_publisher

async def main():
    # Run your full pipeline once
    raw_news = await run_collector()
    summaries = await run_summarizer(raw_news)
    tagged_data = await run_tagger(summaries)
    await run_publisher(tagged_data)

if __name__ == "__main__":
    asyncio.run(main())
