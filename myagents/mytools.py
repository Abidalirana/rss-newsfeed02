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
