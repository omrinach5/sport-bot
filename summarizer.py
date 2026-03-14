import re
import time

import google.generativeai as genai

PROMPT_TEMPLATE = """אתה עוזר ספורט אישי. קיבלת תוכן כתבות מאתר ספורט 5.

המשתמש מתעניין אך ורק ב:
🏀 כדורסל (NBA, יורוליג, ליגת העל בכדורסל, כל הכדורסל)
🎾 טניס (כל הטניס)
⚽ כדורגל: רק ליגת העל הישראלית וליגת האלופות. שום ליגה אחרת!

התעלם לחלוטין מכל נושא אחר — אין ליגה לאומית, אין כדורגל נשים, אין נוער, אין פורמולה 1, אין MMA, אין פרמייר ליג, אין ליגה ספרדית.

הכתבות:
{articles_text}

צור סיכום בעברית בפורמט HTML.

כללים:
- קבץ לפי ליגה/תחרות ספציפית
- כל פריט חייב לכלול שמות אמיתיים, תוצאות, ציטוטים — לא תיאורים כלליים!
- חובה לכלול את הלינק האמיתי של הכתבה (לא לכתוב "URL" אלא את הלינק עצמו)
- מקסימום 10 פריטים לכל ליגה/תחרות
- כתוב בעברית בלבד
- תגיות HTML מותרות: <b>, <i>, <a href="..."> בלבד. אסור <div>, <span>, <p>, <br>!

פורמט:
<b>🏀 יורוליג</b>
• מכבי ניצחה את ברצלונה 89-76, אבדיה 24 נקודות (<a href="https://www.sport5.co.il/...">לכתבה</a>)

<b>🎾 טניס</b>
• ג'וקוביץ' הודח ברבע הגמר של מיאמי מול סינר 6-3, 7-5 (<a href="https://www.sport5.co.il/...">לכתבה</a>)

<b>⚽ ליגת העל</b>
• הפועל ב"ש ניצחה את מכבי ת"א 1-0, שער של זאורי בדקה 78 (<a href="https://www.sport5.co.il/...">לכתבה</a>)
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
