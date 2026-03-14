from unittest.mock import patch, MagicMock
from summarizer import summarize

FAKE_ARTICLES = [
    {
        "title": "מכבי ניצחה 89-76",
        "url": "https://sport5.co.il/1",
        "category": "basketball",
        "content": "מכבי תל אביב ניצחה את הפועל ירושלים 89-76 ביורוליג.",
    },
    {
        "title": "ליברפול ניצחה",
        "url": "https://sport5.co.il/2",
        "category": "football",
        "content": "ליברפול ניצחה את מנצ'סטר סיטי 2-1 בפרמייר ליג.",
    },
]


@patch("summarizer.genai")
def test_summarize_calls_gemini_with_articles(mock_genai):
    mock_model = MagicMock()
    mock_model.generate_content.return_value = MagicMock(text="summary text")
    mock_genai.GenerativeModel.return_value = mock_model

    result = summarize(FAKE_ARTICLES, api_key="fake-key")

    assert result == "summary text"
    mock_genai.configure.assert_called_once_with(api_key="fake-key")
    call_args = mock_model.generate_content.call_args[0][0]
    assert "מכבי ניצחה 89-76" in call_args
    assert "basketball" in call_args


@patch("summarizer.time.sleep")
@patch("summarizer.genai")
def test_summarize_retries_on_failure(mock_genai, mock_sleep):
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = [Exception("API error"), MagicMock(text="retry success")]
    mock_genai.GenerativeModel.return_value = mock_model

    result = summarize(FAKE_ARTICLES, api_key="fake-key")
    assert result == "retry success"
    assert mock_model.generate_content.call_count == 2
