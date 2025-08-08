PS D:\Custom_News_Flow_02_project>
PS D:\Custom_News_Flow_02_project> dir


    Directory: D:\Custom_News_Flow_02_project


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----          8/8/2025   2:33 PM                .venv
d-----          8/8/2025   3:49 PM                db
d-----          8/8/2025   8:13 PM                myagents
d-----          8/8/2025   2:33 PM                tests
d-----          8/8/2025   2:33 PM                __pycache__
-a----          8/8/2025   3:49 PM            146 .env
-a----         7/30/2025   1:06 AM            109 .gitignore
-a----         7/30/2025   1:06 AM              5 .python-version
-a----          8/1/2025  10:48 AM            388 api_server.py
-a----          8/2/2025   8:05 PM            366 main.py
-a----          8/1/2025  10:43 AM            421 pyproject.toml
-a----          8/8/2025   9:21 PM              0 README.md
-a----          8/8/2025   3:49 PM           2608 requirements.txt
-a----          8/1/2025  10:17 AM            458 scheduler.py
-a----          8/1/2025  10:43 AM         180652 uv.lock


PS D:\Custom_News_Flow_02_project> cd myagents
PS D:\Custom_News_Flow_02_project\myagents> dir


    Directory: D:\Custom_News_Flow_02_project\myagents


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----          8/8/2025   2:33 PM                .venv
d-----          8/8/2025   5:40 PM                __pycache__
-a----          8/8/2025   8:07 PM           6126 collectoragent.py
-a----          8/8/2025   8:05 PM           4624 mainagent.py
-a----          8/8/2025   7:42 PM           1677 summarizeragent.py
-a----          8/8/2025   8:13 PM           2323 taggeragnet.py
-a----         7/30/2025   1:12 AM              0 __init__.py


PS D:\Custom_News_Flow_02_project\myagents> 
===========================================================================================
============================================================================================
# collectoragent.py
import os
import asyncio
import hashlib
import httpx
import feedparser
from typing import List
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv
from agents import Agent, function_tool
from openai import AsyncOpenAI

# === ENV ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

# === CONFIG ===
from agents import OpenAIChatCompletionsModel

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client)

# === SCHEMAS ===
class FeedOut(BaseModel):
    title: str
    link: HttpUrl
    published: str
    summary: str
    hash: str

class ScrapedNewsOut(BaseModel):
    title: str
    url: HttpUrl
    published_at: str

# === TOOLS ===
@function_tool
async def strip_html_tags(text: str) -> str:
    """Clean HTML from summary."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

@function_tool
async def fetch_rss(symbols: List[str], max_results: int = 10) -> List[FeedOut]:
    """Fetch Google News RSS by symbol or keyword."""
    results = []
    for keyword in symbols:
        url = f"https://news.google.com/rss/search?q={keyword}"
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:max_results]:
            summary = await strip_html_tags(entry.get("summary", ""))[:300]
            link = entry.link
            results.append(
                FeedOut(
                    title=entry.title,
                    link=link,
                    published=entry.get("published", ""),
                    summary=summary,
                    hash=hashlib.md5(link.encode()).hexdigest(),
                )
            )
    return results

@function_tool
async def fetch_all_rss(max_per: int = 5) -> List[FeedOut]:
    """Fetch from 40+ predefined RSS feeds."""
    RSS_FEEDS = {
        "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US",
        "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "Nasdaq": "https://www.nasdaq.com/feed/rssoutbound?category=Business",
        "Reuters": "https://www.reutersagency.com/en/reuters-best/rss-feed/",
        "Finextra": "https://www.finextra.com/rss/latestnews.aspx",
        "TheStreet": "https://www.thestreet.com/.rss/full/",
        "Zacks": "https://www.zacks.com/commentary/rss.php",
        "Business Insider": "https://markets.businessinsider.com/rss/news",
        "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Forbes Markets": "https://www.forbes.com/markets/feed/",
        "FXStreet": "https://www.fxstreet.com/rss/news",
        "DailyFX": "https://www.dailyfx.com/feeds/all",
        "Cryptonews": "https://cryptonews.com/news/feed/",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
        "TechCrunch Fintech": "https://techcrunch.com/tag/fintech/feed/",
        "The Economic Times": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "Livemint": "https://www.livemint.com/rss/market",
        "Decrypt": "https://decrypt.co/feed",
        "NewsBTC": "https://www.newsbtc.com/feed/",
        "Tokenist": "https://tokenist.com/feed/",
        "Brave New Coin": "https://bravenewcoin.com/news/feed",
        "Investopedia": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
        "Motley Fool": "https://www.fool.com/feeds/index.aspx?id=foolwatch&format=rss2",
        "ZeroHedge": "https://www.zerohedge.com/fullrss.xml",
        "Trading Economics": "https://tradingeconomics.com/rss/news.aspx",
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Cointelegraph": "https://cointelegraph.com/rss",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "Financial Times": "https://www.ft.com/?format=rss",
        "MoneyControl": "https://www.moneycontrol.com/rss/marketnews.xml",
        "AMBCrypto": "https://ambcrypto.com/feed",
        "Finbold": "https://finbold.com/feed",
        "CryptoGlobe": "https://cryptoglobe.com/feed",
        "Watcher.Guru": "https://watcher.guru/feed",
        "Investing.com News": "https://www.investing.com/rss/news_25.rss",
        "The Block": "https://www.theblock.co/rss",
        "Capital.com": "https://capital.com/news/rss",
    }

    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [client.get(url, follow_redirects=True) for url in RSS_FEEDS.values()]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for (src, url), resp in zip(RSS_FEEDS.items(), responses):
            if isinstance(resp, Exception) or resp.status_code != 200:
                continue
            d = feedparser.parse(resp.text)
            for entry in d.entries[:max_per]:
                summary = await strip_html_tags(entry.get("summary", ""))[:300]
                results.append(
                    FeedOut(
                        title=entry.title,
                        link=entry.link,
                        published=getattr(entry, "published", ""),
                        summary=summary,
                        hash=hashlib.md5(entry.link.encode()).hexdigest(),
                    )
                )
    return results

@function_tool
async def scrape_tradingview_news_flow() -> List[ScrapedNewsOut]:
    """Scrape TradingView news-flow page."""
    url = "https://www.tradingview.com/news-flow/"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    for card in soup.select("div.tv-widget-news__item")[:10]:
        title = card.select_one(".tv-widget-news__headline").get_text(strip=True)
        href = card.select_one("a")["href"]
        full_url = "https://www.tradingview.com" + href
        items.append(
            ScrapedNewsOut(
                title=title,
                url=full_url,
                published_at=card.select_one("time")["datetime"],
            )
        )
    return items

@function_tool
async def filter_new(items: List[FeedOut], seen_hashes: set) -> List[FeedOut]:
    """Return only new items based on hash."""
    return [i for i in items if i.hash not in seen_hashes]

# === AGENT ===
collector = Agent(
    name="CollectorAgent",
    instructions="""
You are a high-performance news collector.
- Use `fetch_all_rss` to get top stories from 40+ RSS sources.
- Use `fetch_rss` to get symbol-specific Google News.
- Use `scrape_tradingview_news_flow` for TradingView headlines.
- Use `filter_new` to deduplicate based on hash.
Return clean, deduplicated, and summarized news items.
""",
    tools=[
        fetch_all_rss,
        fetch_rss,
        scrape_tradingview_news_flow,
        filter_new,
        strip_html_tags,
    ],
    model=model,
)

# === DEMO ===
if __name__ == "__main__":
    async def demo():
        print("🧪 CollectorAgent Demo")
        all_news = await fetch_all_rss()
        filtered = await filter_new(all_news, set())
        print(f"📰 Collected {len(filtered)} unique items")
        for i, item in enumerate(filtered[:3], 1):
            print(f"{i}. {item.title} — {item.link}")

    asyncio.run(demo())

======================================================================================
=======================================================================================
02-
# myagents/summarizeragent.py

import os
import asyncio
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel, function_tool


# === Load env ===
load_dotenv()
set_tracing_disabled(True)

# === External Gemini model ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# === Tool ===
@function_tool
def summarize_text(items: List[FeedOut]) -> List[FeedOut]:
    """Dummy summarizer - just returns items"""
    return items

#=============
class FeedOut(BaseModel):
    title: str
    link: HttpUrl
    published: str
    summary: str
    hash: str

# === Agent ===
summarizer = Agent(
    name="SummarizerAgent",
    instructions="""
        Summarize the excerpt into ≤3 bullet points (≤120 characters each).
        Extract relevant stock symbols (e.g., AAPL, TSLA).
        Tag the article with topics: earnings, macro, analyst_rating, etc.
        Respond in strict JSON format using the FeedOut schema.
    """,
    model=model,
    tools=[summarize_text],
    output_type=FeedOut  # ✅ Using FeedOut from mytools.py
)

# === Runner ===
async def run_summarizer(items: list[dict]) -> list[FeedOut]:
    runner = Runner(agent=summarizer)
    return await runner.run(items)
====================================================================================
===========================================================================================
03-
# agents/taggeragent.py


import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio

from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, function_tool, Runner, OpenAIChatCompletionsModel

# ========= Load environment ========= #
load_dotenv()

# ========= Gemini Client Setup ========= #
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-pro",
    openai_client=external_client
)

# ========= Schemas ========= #
class NewsItemInput(BaseModel):
    title: str
    summary: str

class TaggedNews(BaseModel):
    symbols: List[str]
    tags: List[str]

# ========= Agent ========= #
tagger_agent = Agent(
    name="TaggerAgent",
    model=model,
    instructions="""
You are a financial tagging assistant.

Given a news `title` and `summary`, extract:
1. Any stock **symbols** (e.g., AAPL, TSLA, MSFT)
2. Relevant **tags** such as: 'earnings', 'macro', 'fed', 'AI', 'tech', 'energy', etc.

Only return symbols clearly mentioned or implied (e.g., Apple → AAPL).
Respond only with a clean, structured JSON like:
{
  "symbols": ["AAPL"],
  "tags": ["earnings", "AI"]
}
"""
)

# ========= Test Function ========= #
async def test_tagger():
    news = NewsItemInput(
        title="Apple beats Q2 earnings expectations with strong iPhone sales",
        summary="Apple Inc. reported better-than-expected Q2 earnings due to a surge in iPhone demand, sending AAPL shares higher."
    )
    messages = [{"role": "user", "content": f"Title: {news.title}\n\nSummary: {news.summary}"}]
    result = await Runner.run(tagger_agent, messages)
    print("⏹ Final output:")
    print(result.final_output)

# ========= Async Runner ========= #
# ========= Async Runner ========= #
if __name__ == "__main__":
    try:
        asyncio.run(test_tagger())
    except Exception as e:
        print(f"❌ Error running tagger agent: {e}")

===========================================================================================
===========================================================================================
===========================================================================================
04-# --- mainagent.py ---
import sys
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- AGENT PLATFORM IMPORTS ---
from agents import (
    Agent, handoff, HandoffInputData, Runner,
    set_tracing_disabled, OpenAIChatCompletionsModel
)
from agents.extensions import handoff_filters

# --- AGENT COMPONENTS ---
from myagents.collectoragent import collector
from myagents.summarizeragent import summarizer
from myagents.taggeragnet import tagger_agent

# --- DATABASE ---
from db.mydatabase01 import save_feed_items_to_db

# ✅ Result wrapper
@dataclass
class AgentResult:
    final_output: str
    new_items: List[Any]
    metadata: Optional[Dict[str, Any]] = None

# ✅ Feed input model
class FeedInput(BaseModel):
    symbols: List[str]
    max_results: int
    filters: List[str] | None = None

# ✅ Converts FeedInput to messages
class FeedInputConverter:
    @staticmethod
    def to_messages(inputs: List[FeedInput]) -> List[dict]:
        messages = []
        for inp in inputs:
            msg = (
                f"Fetch news for: {', '.join(inp.symbols)}\n"
                f"Max results: {inp.max_results}\n"
                f"Filters: {', '.join(inp.filters) if inp.filters else 'None'}"
            )
            messages.append({"role": "user", "content": msg})
        return messages

# ✅ Filter before summarizer agent
def to_summarizer_filter(h: HandoffInputData) -> HandoffInputData:
    h = handoff_filters.remove_all_tools(h)
    return HandoffInputData(
        input_history=h.input_history[-1:],
        pre_handoff_items=(),
        new_items=h.new_items,
    )

# ✅ Load environment variables
load_dotenv()
set_tracing_disabled(True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing in .env")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# ✅ Main Agent
main_agent = Agent(
    name="MainAgent",
    model=model,
    instructions="""You are MainAgent. Follow this sequence:
1. Handoff to CollectorAgent to fetch news items.
2. Handoff collected items to SummarizerAgent.
3. Handoff final items to TaggerAgent.
""",
    handoffs=[
        handoff(collector),
        handoff(summarizer, input_filter=to_summarizer_filter),
        handoff(tagger_agent),
    ],
)

# ✅ Runner
async def run_main_agent_test():
    test_input = [FeedInput(
        symbols=["openai", "chatgpt"],
        max_results=2,
        filters=None
    )]

    messages = FeedInputConverter.to_messages(test_input)
    result = await Runner.run(main_agent, input=messages)

    valid_items = [
        item for item in result.new_items
        if hasattr(item, "link") and hasattr(item, "title") and item.link and item.title
    ]

    metadata = {
        "agent": "MainAgent",
        "items_collected": len(valid_items),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    custom_result = AgentResult(
        final_output=result.final_output,
        new_items=valid_items,
        metadata=metadata
    )

    print("\n✅ Final Output from MainAgent:\n")
    print(custom_result.final_output)
    print("\n📊 Metadata:", metadata)

    if valid_items:
        print(f"\n🧾 Valid Feed Items ({len(valid_items)}):")
        for i, item in enumerate(valid_items, 1):
            print(f"\n{i}. 📰 {item.title}")
            print(f"🔗 {item.link}")
            print(f"📅 {getattr(item, 'published', 'N/A')}")
            print("-" * 40)

        await save_feed_items_to_db(valid_items)
        print(f"\n💾 {len(valid_items)} valid items saved to DB.")
    else:
        print("\n⚠️ No valid items to save.")

# ✅ Export for external use
run_main_agent = run_main_agent_test

# ✅ Entry point
if __name__ == "__main__":
    try:
        asyncio.run(run_main_agent_test())
    except RuntimeError:
        # For environments with a running loop (e.g., Jupyter)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_main_agent_test())
=======================================================================================
