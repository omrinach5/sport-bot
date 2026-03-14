from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from scraper import scrape_categories, fetch_article_content, filter_recent, _extract_timestamp

FAKE_BASKETBALL_HTML = """
<html><body>
<a href="/articles/basketball/123.aspx"><h3>מכבי ניצחה את הפועל 89-76</h3></a>
<a href="/articles/basketball/124.aspx"><h3>שחקן חדש הצטרף למכבי תל אביב</h3></a>
<a href="/short">קצר</a>
</body></html>
"""


def _mock_response(html):
    resp = MagicMock()
    resp.text = html
    resp.status_code = 200
    return resp


@patch("scraper.requests.get")
def test_scrape_categories_extracts_articles(mock_get):
    mock_get.return_value = _mock_response(FAKE_BASKETBALL_HTML)
    articles = scrape_categories(["https://www.sport5.co.il/world.aspx?FolderID=4467"])
    assert len(articles) == 2
    assert articles[0]["title"] == "מכבי ניצחה את הפועל 89-76"
    assert articles[0]["url"] == "https://www.sport5.co.il/articles/basketball/123.aspx"
    assert articles[0]["category"] == "basketball"


@patch("scraper.requests.get")
def test_scrape_categories_skips_short_titles(mock_get):
    mock_get.return_value = _mock_response(FAKE_BASKETBALL_HTML)
    articles = scrape_categories(["https://www.sport5.co.il/world.aspx?FolderID=4467"])
    titles = [a["title"] for a in articles]
    assert "קצר" not in titles


@patch("scraper.requests.get")
def test_scrape_categories_deduplicates(mock_get):
    mock_get.return_value = _mock_response(FAKE_BASKETBALL_HTML)
    articles = scrape_categories([
        "https://www.sport5.co.il/basketball.aspx",
        "https://www.sport5.co.il/basketball.aspx",
    ])
    assert len(articles) == 2


FAKE_ARTICLE_HTML = """
<html><body>
<article>
    <p>מכבי תל אביב ניצחה את הפועל ירושלים 89-76 במשחק מרתק ביורוליג.</p>
    <p>דני אבדיה הוביל עם 24 נקודות ו-8 אסיסטים.</p>
    <p>פרסומת שלא צריך לקרוא</p>
</article>
</body></html>
"""


@patch("scraper.time.sleep")
@patch("scraper.requests.get")
def test_fetch_article_content_extracts_paragraphs(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(FAKE_ARTICLE_HTML)
    articles = [{"title": "Test", "url": "https://sport5.co.il/article/1", "category": "basketball", "content": "", "timestamp": None}]
    result = fetch_article_content(articles, max_articles=1)
    assert "89-76" in result[0]["content"]
    assert "24 נקודות" in result[0]["content"]


@patch("scraper.time.sleep")
@patch("scraper.requests.get")
def test_fetch_article_content_limits_articles(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(FAKE_ARTICLE_HTML)
    articles = [
        {"title": f"Article {i}", "url": f"https://sport5.co.il/article/{i}", "category": "basketball", "content": "", "timestamp": None}
        for i in range(30)
    ]
    result = fetch_article_content(articles, max_articles=25)
    assert len(result) == 25


FAKE_ARTICLE_WITH_TIME = """
<html><body>
<time datetime="2026-03-14T10:30:00">14/03/2026 10:30</time>
<article><p>Some content here for the article body text.</p></article>
</body></html>
"""

FAKE_ARTICLE_NO_TIME = """
<html><body>
<article><p>Article without any timestamp element at all.</p></article>
</body></html>
"""


def test_extract_timestamp_from_time_element():
    soup = BeautifulSoup(FAKE_ARTICLE_WITH_TIME, "html.parser")
    ts = _extract_timestamp(soup)
    assert ts is not None
    assert ts.year == 2026
    assert ts.month == 3
    assert ts.day == 14


def test_extract_timestamp_returns_none_when_missing():
    soup = BeautifulSoup(FAKE_ARTICLE_NO_TIME, "html.parser")
    ts = _extract_timestamp(soup)
    assert ts is None


def test_filter_recent_keeps_recent_articles():
    now = datetime.now(timezone.utc)
    articles = [
        {"title": "Recent", "timestamp": now - timedelta(hours=2), "content": "x", "url": "u", "category": "c"},
        {"title": "Old", "timestamp": now - timedelta(hours=20), "content": "x", "url": "u", "category": "c"},
        {"title": "No time", "timestamp": None, "content": "x", "url": "u", "category": "c"},
    ]
    result = filter_recent(articles, hours=12)
    titles = [a["title"] for a in result]
    assert "Recent" in titles
    assert "Old" not in titles
    assert "No time" in titles
