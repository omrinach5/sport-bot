from unittest.mock import patch, MagicMock
from scraper import scrape_categories

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
