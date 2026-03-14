from unittest.mock import patch, MagicMock
from scraper import scrape_categories, fetch_article_content

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
    articles = scrape_categories(["https://www.sport5.co.il/basketball.aspx"])
    assert len(articles) == 2
    assert articles[0]["title"] == "מכבי ניצחה את הפועל 89-76"
    assert articles[0]["url"] == "https://www.sport5.co.il/articles/basketball/123.aspx"
    assert articles[0]["category"] == "basketball"


@patch("scraper.requests.get")
def test_scrape_categories_skips_short_titles(mock_get):
    mock_get.return_value = _mock_response(FAKE_BASKETBALL_HTML)
    articles = scrape_categories(["https://www.sport5.co.il/basketball.aspx"])
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
