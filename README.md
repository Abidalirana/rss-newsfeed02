📰 RSS News Feed Pipeline
This project collects news from RSS feeds, summarizes them, tags them, and publishes them using scheduled jobs and an API.

📂 Project Structure
bash
Copy
Edit
.
├── api_server.py            # FastAPI server for accessing news data
├── scheduler.py             # Runs the pipeline automatically on schedule
├── main.py                  # Main pipeline runner
├── myagents/
│   ├── collectoragent.py    # Fetches RSS feeds
│   ├── summarizeragent.py   # Summarizes articles
│   ├── taggeragent.py       # Adds tags to news items
│   ├── publisheragent.py    # Publishes news (marks as published)
│   └── db.py                # Database models & save logic
⚙️ Requirements
Python 3.11+

PostgreSQL (running locally or remotely)

pip or uv package manager

📦 Installation
Clone the repository

bash
Copy
Edit
git clone https://github.com/Abidalirana/rss-news-feed.git
cd rss-news-feed
Install dependencies

Using pip:

nginx
Copy
Edit
pip install -r requirements.txt
Or using uv:

nginx
Copy
Edit
uv pip install -r requirements.txt
Set up the database

Create a PostgreSQL database:

pgsql
Copy
Edit
CREATE DATABASE newsfeed;
Update the connection URL in myagents/db.py:

ini
Copy
Edit
DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost/newsfeed"
Create tables:

arduino
Copy
Edit
uv run python -m myagents.db
🚀 Running the Project
1. Run the API server
arduino
Copy
Edit
uv run api_server.py
API will start on: http://127.0.0.1:8000

Example endpoints:

/news → get news list

/news/{id} → get a single news item

2. Run the scheduler
arduino
Copy
Edit
uv run scheduler.py
Runs the pipeline automatically every 1 minute (configurable inside scheduler.py).

Scheduler will:

Collect new RSS feed data

Summarize

Tag

Publish (mark as published in DB)

3. Run the pipeline manually
arduino
Copy
Edit
uv run main.py
Executes the pipeline once.

🛠 Configuration
Change schedule frequency in scheduler.py:

csharp
Copy
Edit
schedule.every(1).minutes.do(run_async_job)  # change minutes/hours
Change feeds in collectoragent.py.

📝 Notes
Make sure PostgreSQL is running before starting.

First run may take longer because of initial feed collection.

publisher column in DB is False until an item is published.



===

for db 
SELECT * FROM news_items;

SELECT published_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Karachi'
FROM news_items;

==
How to see the data in DB
Since your DB name is newsfeed, you can run:

======
-- Show all columns including publisher status


SELECT id, title, url, published_at, publisher
FROM news_items
ORDER BY published_at DESC;
If you want to see only published ones:

=========
SELECT * 
FROM news_items
WHERE publisher = true
ORDER BY published_at DESC;
====
DELETE FROM news_items;
===
DELETE FROM news_items WHERE publisher = false;
===