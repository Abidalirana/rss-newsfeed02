import asyncio
import time
import schedule
import datetime
from main import main

def run_async_job():
    print(f"⏰ Running job at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.close()

# Run every 10 seconds for testing (change to e.g. every().hour.do(...) for production)
schedule.every(10).seconds.do(run_async_job)

print("📆 Scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(1)
