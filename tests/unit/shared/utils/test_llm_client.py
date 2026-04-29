import pytest
import json
from unittest.mock import patch, MagicMock
from src.shared.utils.llm_client import LLMApiClient

@pytest.fixture
def mock_openai():
    with patch("src.shared.utils.llm_client.OpenAI") as mock:
        yield mock

def test_Initialization_ShouldSetApiKey_WhenEnvVarExists(mock_openai):
    """Verify initialization with API key from environment."""
    # Arrange
    with patch("os.getenv", return_value="fake_key"):
        # Act
        client = LLMApiClient()
        
        # Assert
        mock_openai.assert_called_once_with(api_key="fake_key")
        assert client.model == "gpt-5-mini"

def test_Initialization_ShouldRaiseValueError_WhenApiKeyMissing():
    """Verify that Missing API key raises ValueError."""
    # Act & Assert
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            LLMApiClient()

def test_Generate_ShouldReturnText_WhenValidInputProvided(mock_openai):
    """Verify generate method returns text content."""
    # Arrange
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "  Hello World  "
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate([{"role": "user", "content": "hi"}])
        
        # Assert
        assert result == "Hello World"
        mock_instance.chat.completions.create.assert_called_once()

def test_GenerateJson_ShouldReturnParsedDict_WhenValidInputProvided(mock_openai):
    """Verify generate_json method returns parsed dict."""
    # Arrange
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"key": "value"}'
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}])
        
        # Assert
        assert result == {"key": "value"}
        # Check that json_object format was requested
        args, kwargs = mock_instance.chat.completions.create.call_args
        assert kwargs["response_format"] == {"type": "json_object"}

def test_GenerateJson_ShouldRaiseValueError_WhenResponseIsInvalidJson(mock_openai):
    """Verify that invalid JSON raises ValueError."""
    # Arrange
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = 'Invalid JSON'
    mock_instance.chat.completions.create.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Model returned invalid JSON"):
            client.generate_json([{"role": "user", "content": "hi"}])

def test_GenerateJson_ShouldUseBetaParse_WhenResponseFormatProvided(mock_openai):
    """Verify that beta.chat.completions.parse is used for structured outputs."""
    # Arrange
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_parsed = MagicMock()
    mock_parsed.model_dump.return_value = {"key": "structured"}
    mock_response.choices[0].message.parsed = mock_parsed
    mock_instance.beta.chat.completions.parse.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}], response_format=MagicMock())
        
        # Assert
        assert result == {"key": "structured"}
        mock_instance.beta.chat.completions.parse.assert_called_once()

def test_GenerateJson_ShouldFallbackToJsonLoads_WhenParsedIsNone(mock_openai):
    """Verify fallback to json.loads when parsed is None in beta parse."""
    # Arrange
    mock_instance = mock_openai.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = None
    mock_response.choices[0].message.content = '{"key": "fallback"}'
    mock_instance.beta.chat.completions.parse.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}], response_format=MagicMock())
        
        # Assert
        assert result == {"key": "fallback"}
