# --- mytools.py ---
import feedparser
import hashlib
from typing import List
from agents import function_tool
from pydantic import BaseModel, HttpUrl


# ✅ Output schema

class FeedOut(BaseModel):
    title: str
    link: HttpUrl
    published: str
    summary: str
    hash: str


# ✅ Tools
@function_tool
def fetch_rss(symbols: list[str], max_results: int = 10) -> List[FeedOut]:
    """Fetch RSS feed data based on symbols (keywords)"""
    result = []
    for keyword in symbols:
        url = f"https://news.google.com/rss/search?q={keyword}"
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:max_results]:
            item = FeedOut(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                published=entry.get("published", ""),
                summary=entry.get("summary", ""),
                hash=hashlib.md5(entry.get("link", "").encode()).hexdigest(),
            )
            result.append(item)
    return result


@function_tool
def filter_new(items: List[FeedOut]) -> List[FeedOut]:
    """Dummy filter - return all for now"""
    return items


@function_tool
def scrape_and_compress(items: List[FeedOut]) -> List[FeedOut]:
    """Dummy scraper - just returns original items"""
    return items


@function_tool
def summarize_text(items: List[FeedOut]) -> List[FeedOut]:
    """Dummy summarizer - just returns items"""
    return items


@function_tool
def tag_topics(items: List[FeedOut]) -> List[FeedOut]:
    """Dummy tagger - just returns items"""
    return items
#====for news collector agent 
from bs4 import BeautifulSoup
import requests

class ScrapedNewsOut(BaseModel):
    title: str
    url: HttpUrl
    published_at: str

@function_tool
def scrape_tradingview_news_flow() -> List[ScrapedNewsOut]:
    """Scrape news items from TradingView News Flow page"""
    url = "https://www.tradingview.com/news-flow/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for item in soup.select("div.tv-widget-news__item"):
        title_el = item.select_one(".tv-widget-news__headline")
        time_el = item.select_one("time")
        link_el = item.select_one("a")

        if not title_el or not time_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        published_at = time_el.get("datetime", "")
        full_url = "https://www.tradingview.com" + link_el["href"]

        results.append(ScrapedNewsOut(
            title=title,
            url=full_url,
            published_at=published_at
        ))

    return results
#==================================
@function_tool
def fetch_site_news() -> List[FeedOut]:
    """Fetch news from multiple open-source trading/news platforms."""
    import requests
    from bs4 import BeautifulSoup

    sources = {
        "TradingView": "https://www.tradingview.com/news-flow/",
        "CoinDesk": "https://www.coindesk.com/",
        "Cointelegraph": "https://cointelegraph.com/",
        "CryptoSlate": "https://cryptoslate.com/",
        # Add up to 40+ URLs here
    }

    results = []
    for name, url in sources.items():
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Customize selectors based on website
            for item in soup.find_all('a', limit=5):
                link = item.get('href')
                title = item.get_text(strip=True)
                if title and link:
                    results.append(FeedOut(
                        title=title,
                        link=link if link.startswith("http") else url + link,
                        published="",
                        summary=f"From {name}",
                        hash=hashlib.md5(link.encode()).hexdigest()
                    ))
        except Exception as e:
            print(f"⚠️ Failed to fetch from {name}: {e}")
    return results

