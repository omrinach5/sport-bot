from unittest.mock import patch, MagicMock
from telegram_bot import send_summary, _split_message

LONG_SECTION_1 = "<b>🏀 יורוליג</b>\n• פריט 1\n• פריט 2\n"
LONG_SECTION_2 = "<b>⚽ פרמייר ליג</b>\n• פריט 3\n• פריט 4\n"


def test_split_message_short_message():
    msg = LONG_SECTION_1 + "\n" + LONG_SECTION_2
    parts = _split_message(msg)
    assert len(parts) == 1
    assert parts[0] == msg


def test_split_message_splits_at_section_boundary():
    # Create a message that exceeds 4096 characters
    section1 = "<b>🏀 יורוליג</b>\n" + ("• " + "א" * 200 + "\n") * 15
    section2 = "<b>⚽ פרמייר ליג</b>\n" + ("• " + "ב" * 200 + "\n") * 15
    msg = section1 + "\n" + section2
    parts = _split_message(msg)
    assert len(parts) == 2
    assert "יורוליג" in parts[0]
    assert "פרמייר ליג" in parts[1]


@patch("telegram_bot.requests.post")
def test_send_summary_sends_html(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    send_summary("test message", token="tok", chat_id="123")
    call_json = mock_post.call_args[1]["json"]
    assert call_json["parse_mode"] == "HTML"
    assert call_json["text"] == "test message"
    assert call_json["chat_id"] == "123"
