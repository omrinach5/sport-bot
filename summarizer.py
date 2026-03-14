import re
import time

import google.generativeai as genai

SPORT_PRIORITIES = """העדפות ענפי ספורט של המשתמש:
- עדיפות ראשונה: כדורסל, טניס
- עדיפות שנייה: כדורגל
- שאר הספורט: רק אם חשוב מאוד"""

PROMPT_TEMPLATE = """אתה עוזר ספורט אישי. קיבלת תוכן כתבות מאתר ספורט 5.

{priorities}

הכתבות (כל כתבה כוללת קטגוריית מקור, כותרת, ותוכן):
{articles_text}

צור סיכום ספורט בעברית בפורמט HTML.

כללים חשובים:
- קבץ לפי ליגה/תחרות ספציפית (יורוליג, NBA, ליגת העל, פרמייר ליג, וכו') — לא לפי ענף ספורט כללי
- כל פריט חייב להיות אינפורמטיבי עם פרטים אמיתיים: תוצאות, שמות שחקנים, ציטוטים, העברות
- פורמט כל פריט: נקודה אינפורמטיבית ואז לינק בסוף
- דוגמאות לפריטים טובים:
  • מכבי ניצחה את הפועל 89-76, אבדיה עם 24 נקודות
  • שחקן X עובר לקבוצה Y בעסקה של 5 מיליון
  • מאמן X: "אנחנו מוכנים לפלייאוף"
- דוגמאות לפריטים גרועים (לא לכתוב כך!):
  • עדכוני כדורסל - [לינק]
  • חדשות כדורגל ישראלי - [לינק]
- אל תכלול ליגות/תחרויות ללא חדשות
- מקסימום 20 פריטים סה"כ
- כתוב בעברית בלבד, מימין לשמאל (RTL)
- עבור כתבות מקטגוריה 'general' (דף הבית), קבע את הליגה/תחרות לפי תוכן הכתבה עצמה
- השתמש בפורמט HTML מוגבל בלבד. תגיות מותרות: <b>, <i>, <a href="...">, <code>, <pre>. אסור להשתמש ב-<div>, <span>, <p>, <br>, <ul>, <li> או כל תגית אחרת!
- פורמט הפלט:
  <b>🏀 יורוליג</b>
  • פריט אינפורמטיבי (<a href="URL">קישור</a>)

  <b>⚽ פרמייר ליג</b>
  • פריט אינפורמטיבי (<a href="URL">קישור</a>)
"""


def _sanitize_html(text):
    """Strip HTML tags not supported by Telegram (only <b>, <i>, <a>, <code>, <pre> allowed)."""
    # Remove unsupported tags but keep their content
    text = re.sub(r'</?(?!b|/b|i|/i|a|/a|code|/code|pre|/pre)[^>]+>', '', text)
    return text.strip()


def summarize(articles, api_key):
    """Summarize articles using Gemini. Retries once on failure."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    articles_text = "\n\n".join([
        f"[קטגוריה: {a['category']}]\nכותרת: {a['title']}\nתוכן: {a.get('content', '')}\nלינק: {a['url']}"
        for a in articles
    ])

    prompt = PROMPT_TEMPLATE.format(
        priorities=SPORT_PRIORITIES,
        articles_text=articles_text,
    )

    for attempt in range(2):
        try:
            response = model.generate_content(prompt)
            return _sanitize_html(response.text)
        except Exception as e:
            if attempt == 0:
                print(f"Gemini API error, retrying in 5s: {e}")
                time.sleep(5)
            else:
                raise
