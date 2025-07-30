# scheduler.py

import schedule
import time
from main import main

# Schedule it every 1 hour (or whatever you want)
schedule.every(1).hours.do(main)

print("📆 Scheduler started...")

while True:
    schedule.run_pending()
    time.sleep(1)
