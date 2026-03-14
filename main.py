import os
import sys

from scraper import scrape_categories, fetch_article_content, filter_recent
from summarizer import summarize
from telegram_bot import send_summary

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


def main():
    # 1. Scrape category pages
    print("Scraping sport5.co.il categories...")
    articles = scrape_categories()
    print(f"Found {len(articles)} article links")

    if not articles:
        send_summary(
            "לא הצלחתי לאסוף חדשות היום",
            token=TELEGRAM_TOKEN,
            chat_id=TELEGRAM_CHAT_ID,
        )
        return

    # 2. Fetch article content
    print("Fetching article content...")
    articles = fetch_article_content(articles)

    # 3. Filter to last 12 hours
    articles = filter_recent(articles, hours=12)
    print(f"{len(articles)} articles from last 12 hours")

    if not articles:
        send_summary(
            "אין עדכוני ספורט חדשים ב-12 השעות האחרונות",
            token=TELEGRAM_TOKEN,
            chat_id=TELEGRAM_CHAT_ID,
        )
        return

    # 4. Summarize with Gemini
    print("Summarizing with Gemini...")
    try:
        summary = summarize(articles, api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Failed to summarize: {e}")
        sys.exit(1)

    # 5. Send to Telegram
    print("Sending to Telegram...")
    header = "<b>📊 סיכום ספורט - ספורט 5</b>\n\n"
    try:
        send_summary(header + summary, token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")
        sys.exit(1)
    print("Done!")


if __name__ == "__main__":
    main()
