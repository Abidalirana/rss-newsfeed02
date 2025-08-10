RSS News Feed Agents
A modular Python project that collects, summarizes, and tags financial news from multiple RSS feeds using AI (Google Gemini API). The pipeline stores processed news into a PostgreSQL database.

Features
Collector Agent: Fetches news articles from specified RSS feeds or APIs.

Summarizer Agent: Summarizes news articles into concise bullet points using AI.

Tagger Agent: Automatically extracts relevant stock symbols and topic tags from news.

Scheduler: Automates the pipeline to run at scheduled intervals.

Database Storage: Stores news items with metadata, summaries, tags, and symbols in PostgreSQL.

Async & Modular: Built with asyncio and designed for easy extension.

Requirements
Python 3.9+

PostgreSQL database

Dependencies listed in requirements.txt

API Key for Google Gemini (set in .env)

Setup
Clone the repo:

bash
Copy
Edit
git clone https://github.com/Abidalirana/rss-news-feed.git
cd rss-news-feed
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Configure PostgreSQL and update DATABASE_URL in .env file.

Add your Gemini API key in .env:

env
Copy
Edit
GEMINI_API_KEY=your_api_key_here
Usage
Run full pipeline once
bash
Copy
Edit
uv run mainagent.py
or run from    uv run main.py 
Run scheduler to automate
bash
Copy
Edit
uv run scheduler.py
Project Structure
myagents/ — Contains agents for collecting, summarizing, tagging, and database interaction.

mainagent.py — Runs the full pipeline (collector → summarizer → tagger → DB).

scheduler.py — Scheduler that triggers the pipeline periodically.

.env — Environment variables for keys and DB config.

Notes
Make sure your PostgreSQL server is running.

Gemini API usage may incur costs; monitor usage accordingly.

Currently designed for financial news feeds, but can be extended.




===================================================================================================================
===================================================================================================================
===================================================================================================================v
summaray of db
The project stores news articles in a PostgreSQL table `news_items` with 10 columns:
- id: unique identifier
- title: article title
- source: news source name
- published_at: publication date/time (set by collector)
- content: full article text (set by collector)
- summary: summarized text (set by summarizer)
- tags: list of tags extracted (set by tagger)
- symbols: list of stock symbols extracted (set by tagger)
- url: unique article URL
- provider: source type (e.g. "rss", "html-scraper")

The data flow is:
1. Collector fetches news, saves new articles including published_at.
2. Summarizer generates and updates summaries.
3. Tagger extracts and updates tags and symbols.


===================================================================================================================
===================================================================================================================
===================================================================================================================v


checking data in  db eaver 

SELECT * FROM news_items ORDER BY published_at DESC LIMIT 20;
