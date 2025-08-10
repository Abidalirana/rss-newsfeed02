import asyncio
import time
import schedule
import datetime
from main import run_pipeline  # Adjust if your pipeline function is in another file

async def run_async_job():
    print(f"⏰ Running job at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await run_pipeline()

# Schedule to run every 1 minute
schedule.every(1).minutes.do(lambda: asyncio.run(run_async_job()))

print("📆 Scheduler started... (will run every 1 minute)")

while True:
    schedule.run_pending()
    time.sleep(1)
