import re
import time
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

CATEGORY_URLS = [
    "https://www.sport5.co.il/basketball.aspx",
    "https://www.sport5.co.il/tennis.aspx",
    "https://www.sport5.co.il/football.aspx",
]

CATEGORY_MAP = {
    "basketball": "basketball",
    "tennis": "tennis",
    "football": "football",
}


def _detect_category(url):
    """Detect sport category from URL."""
    for keyword, category in CATEGORY_MAP.items():
        if keyword in url:
            return category
    return "general"


def scrape_categories(urls=None):
    """Scrape sport5 category pages for article headlines and links."""
    if urls is None:
        urls = CATEGORY_URLS

    articles = []
    seen_titles = set()

    for url in urls:
        category = _detect_category(url)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup.find_all(["h1", "h2", "h3", "a"], limit=50):
                text = tag.get_text(strip=True)
                href = tag.get("href", "")

                if len(text) <= 20 or text in seen_titles:
                    continue

                seen_titles.add(text)
                full_url = (
                    href if href.startswith("http")
                    else f"https://www.sport5.co.il{href}"
                )
                articles.append({
                    "title": text,
                    "url": full_url if href else url,
                    "category": category,
                    "content": "",
                    "timestamp": None,
                })
            count = len(articles) - len(seen_titles) + len(seen_titles)
            print(f"  [{category}] found articles from {url}")
        except Exception as e:
            print(f"Warning: failed to scrape {url}: {e}")

    print(f"Total scraped: {len(articles)} articles")
    return articles


IST = timezone(timedelta(hours=3))


def _extract_timestamp(soup):
    """Try to extract article publish timestamp from HTML."""
    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        try:
            dt_str = time_tag["datetime"]
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
            return dt.astimezone(timezone.utc)
        except (ValueError, KeyError):
            pass

    for meta_name in ["article:published_time", "og:updated_time", "pubdate"]:
        meta = soup.find("meta", attrs={"property": meta_name}) or soup.find("meta", attrs={"name": meta_name})
        if meta and meta.get("content"):
            try:
                dt = datetime.fromisoformat(meta["content"].replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=IST)
                return dt.astimezone(timezone.utc)
            except (ValueError, KeyError):
                pass

    return None


def filter_recent(articles, hours=12):
    """Keep only articles from the last N hours. Include articles with no timestamp."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [a for a in articles if a["timestamp"] is None or a["timestamp"] >= cutoff]


def fetch_article_content(articles, max_articles=25):
    """Fetch first 2-3 paragraphs of content for each article."""
    results = [dict(a) for a in articles[:max_articles]]

    for article in results:
        try:
            response = requests.get(article["url"], headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            paragraphs = []
            for p in soup.find_all("p", limit=5):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    paragraphs.append(text)
                if len(paragraphs) >= 3:
                    break

            article["content"] = " ".join(paragraphs)
            article["timestamp"] = _extract_timestamp(soup)
            time.sleep(0.3)
        except Exception as e:
            print(f"Warning: failed to fetch {article['url']}: {e}")

    return results
