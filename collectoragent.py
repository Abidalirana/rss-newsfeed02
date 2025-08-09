# collector.py (Cleaned: No Agent, Pure Python Script)
import asyncio
import hashlib
import httpx
import feedparser
from typing import List
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl

# === SCHEMAS ===
class FeedOut(BaseModel):
    title: str
    link: HttpUrl
    published: str
    summary: str
    hash: str

# === HELPERS ===
def strip_html_tags(text: str) -> str:
    """Clean HTML from summary."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

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
                summary = strip_html_tags(entry.get("summary", ""))[:300]
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

# === DEMO ===
if __name__ == "__main__":
    async def demo():
        print("\n📰 Fetching RSS feeds...")
        items = await fetch_all_rss()
        print(f"✅ Got {len(items)} items\n")
        for i, item in enumerate(items[:5], 1):
            print(f"{i}. {item.title} — {item.link}")

    asyncio.run(demo())
