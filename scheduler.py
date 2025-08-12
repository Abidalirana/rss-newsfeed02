import asyncio
import datetime
from main import run_pipeline  # Adjust if needed


async def job():
    print(f"⏰ Running job at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await run_pipeline()


async def scheduler():
    while True:
        await job()
        await asyncio.sleep(10)  # Wait 10 seconds before next run


if __name__ == "__main__":
    print("📆 Scheduler started... (will run every 10 seconds)")
    asyncio.run(scheduler())
