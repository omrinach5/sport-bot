import re

import requests

TELEGRAM_MAX_LENGTH = 4096


def _split_message(message):
    """Split message at section boundaries if it exceeds Telegram's limit."""
    if len(message) <= TELEGRAM_MAX_LENGTH:
        return [message]

    # Split on newline before bold section headers
    sections = re.split(r"\n(?=<b>)", message)

    parts = []
    current = ""
    for section in sections:
        test = current + ("\n" if current else "") + section
        if len(test) > TELEGRAM_MAX_LENGTH and current:
            parts.append(current.strip())
            current = section
        else:
            current = test

    if current.strip():
        parts.append(current.strip())

    return parts if parts else [message]


def send_summary(message, token, chat_id):
    """Send HTML message to Telegram, splitting if necessary. Retries once on failure."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    parts = _split_message(message)

    for part in parts:
        for attempt in range(2):
            response = requests.post(url, json={
                "chat_id": chat_id,
                "text": part,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            })
            if response.status_code == 200:
                print(f"Message sent ({len(part)} chars)")
                break
            elif attempt == 0:
                print(f"Telegram error, retrying: {response.text}")
            else:
                print(f"Telegram error after retry: {response.text}")
                raise RuntimeError(f"Telegram API failed: {response.text}")
