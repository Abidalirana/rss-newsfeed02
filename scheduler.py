# scheduler.py

import asyncio
import time
import schedule
import datetime
from main import main

def run_async_job():
    print(f"⏰ Running job at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    asyncio.run(main())

# Run every 10 seconds for testing (later change back to hours)
schedule.every(10).seconds.do(run_async_job)

print("📆 Scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(1)

