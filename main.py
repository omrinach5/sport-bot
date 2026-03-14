import os
import requests
from bs4 import BeautifulSoup
import anthropic

# --- Config ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SPORT_PRIORITIES = """
העדפות ענפי ספורט של המשתמש:
- עדיפות ראשונה: כדורסל, טניס
- עדיפות שנייה: כדורגל
- שאר הספורט: רק אם חשוב מאוד
"""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_sport5():
    """Scrape articles from sport5.co.il"""
    articles = []
    
    urls_to_scrape = [
        "https://www.sport5.co.il/basketball.aspx",
        "https://www.sport5.co.il/tennis.aspx", 
        "https://www.sport5.co.il/football.aspx",
        "https://www.sport5.co.il/",
    ]
    
    seen_titles = set()
    
    for url in urls_to_scrape:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find article links and titles
            for tag in soup.find_all(["h1", "h2", "h3", "a"], limit=50):
                text = tag.get_text(strip=True)
                href = tag.get("href", "")
                
                if len(text) > 20 and text not in seen_titles:
                    seen_titles.add(text)
                    full_url = href if href.startswith("http") else f"https://www.sport5.co.il{href}"
                    articles.append({
                        "title": text,
                        "url": full_url if href else url,
                        "source": url
                    })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    return articles[:60]  # Limit to 60 articles


def summarize_with_claude(articles):
    """Send articles to Claude for summarization"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    articles_text = "\n".join([
        f"- {a['title']} | {a['url']}"
        for a in articles
    ])
    
    prompt = f"""אתה עוזר ספורט אישי. קיבלת רשימת כתבות מאתר ספורט 5.
    
{SPORT_PRIORITIES}

הכתבות:
{articles_text}

צור סיכום יומי בעברית בפורמט הזה:

🏀 *כדורסל וטניס* (עדיפות ראשונה)
• [סיכום קצר של כל כתבה רלוונטית + לינק]

⚽ *כדורגל*
• [סיכום קצר של כתבות רלוונטיות + לינק]

📰 *שאר הספורט* (רק אם חשוב מאוד)
• [אם יש משהו בולט מאוד]

כללים:
- כתוב בעברית
- לכל פריט הוסף לינק רלוונטי
- קצר וענייני
- אם אין חדשות בענף מסוים - כתוב "אין עדכונים חשובים"
- מקסימום 20 פריטים סה"כ"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text


def send_telegram(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Split if too long (Telegram limit is 4096 chars)
    if len(message) > 4000:
        message = message[:4000] + "\n\n... [קוצר בגלל אורך]"
    
    response = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })
    
    if response.status_code == 200:
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Error sending message: {response.text}")


def main():
    print("🔍 Scraping sport5.co.il...")
    articles = scrape_sport5()
    print(f"Found {len(articles)} articles")
    
    print("🤖 Summarizing with Claude...")
    summary = summarize_with_claude(articles)
    
    print("📱 Sending to Telegram...")
    header = "📊 *סיכום ספורט יומי - ספורט 5*\n\n"
    send_telegram(header + summary)


if __name__ == "__main__":
    main()
