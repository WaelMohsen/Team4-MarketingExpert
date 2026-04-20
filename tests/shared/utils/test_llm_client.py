import pytest
import json
from unittest.mock import patch, MagicMock
from src.shared.utils.llm_client import LLMApiClient

@pytest.fixture
def mock_openai():
    with patch("src.shared.utils.llm_client.OpenAI") as mock:
        yield mock

def test_llm_api_client_initialization(mock_openai):
    """Verify initialization with API key from environment."""
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        mock_openai.assert_called_once_with(api_key="fake_key")
        assert client.model == "gpt-5-mini"

def test_llm_api_client_missing_key():
    """Verify that Missing API key raises ValueError."""
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            LLMApiClient()

def test_generate_text(mock_openai):
    """Verify generate method returns text content."""
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "  Hello World  "
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        result = client.generate([{"role": "user", "content": "hi"}])
        
        assert result == "Hello World"
        mock_instance.chat.completions.create.assert_called_once()

def test_generate_json(mock_openai):
    """Verify generate_json method returns parsed dict."""
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"key": "value"}'
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        result = client.generate_json([{"role": "user", "content": "hi"}])
        
        assert result == {"key": "value"}
        # Check that json_object format was requested
        args, kwargs = mock_instance.chat.completions.create.call_args
        assert kwargs["response_format"] == {"type": "json_object"}

def test_generate_json_invalid_response(mock_openai):
    """Verify that invalid JSON raises ValueError."""
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = 'Invalid JSON'
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        with pytest.raises(ValueError, match="Model returned invalid JSON"):
            client.generate_json([{"role": "user", "content": "hi"}])
