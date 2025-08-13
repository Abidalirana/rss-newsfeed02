from myagents.collectoragent import run_collector
from myagents.summarizeragent import run_summarizer
from myagents.taggeragent import run_tagger
from myagents.publisheragent import run_publisher
from myagents.db import create_tables  # import create_tables from your db module

async def run_pipeline():
    collected = await run_collector()
    summarized = await run_summarizer(collected)
    tagged = await run_tagger(summarized)
    published_count = await run_publisher()
    print(f"Pipeline finished: {len(tagged)} items saved, {published_count} items published.")

async def startup():
    await create_tables()  # create tables on startup
    print("Tables created or already exist.")
    await run_pipeline()

if __name__ == "__main__":
    import asyncio
    asyncio.run(startup())
