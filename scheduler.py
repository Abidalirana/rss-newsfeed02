import asyncio
import datetime
from main import run_pipeline  # Adjust if needed

async def job():
    print(f"⏰ Running job at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await run_pipeline()

async def scheduler():
    while True:
        await job()
        await asyncio.sleep(6 * 60 * 60)  # Sleep for 6 hours

if __name__ == "__main__":
    print("📆 Scheduler started... (will run every 6 hours)")
    asyncio.run(scheduler())
