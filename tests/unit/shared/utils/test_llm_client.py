import pytest
import json
from unittest.mock import patch, MagicMock
from src.shared.utils.llm_client import LLMApiClient

@pytest.fixture
def mock_chat_openai():
    with patch("src.shared.utils.llm_client.ChatOpenAI") as mock:
        yield mock

def test_Initialization_ShouldSetApiKey_WhenEnvVarExists(mock_chat_openai):
    """Verify initialization with API key from environment."""
    # Arrange
    with patch("os.getenv", return_value="fake_key"):
        # Act
        client = LLMApiClient()
        
        # Assert
        mock_chat_openai.assert_called_once_with(
            model="gpt-5-mini",
            api_key="fake_key",
            max_tokens=4000
        )
        assert client.model == "gpt-5-mini"

def test_Initialization_ShouldRaiseValueError_WhenApiKeyMissing():
    """Verify that Missing API key raises ValueError."""
    # Act & Assert
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            LLMApiClient()

def test_Generate_ShouldReturnText_WhenValidInputProvided(mock_chat_openai):
    """Verify generate method returns text content."""
    # Arrange
    mock_instance = mock_chat_openai.return_value
    mock_response = MagicMock()
    mock_response.content = "  Hello World  "
    mock_instance.invoke.return_value = mock_response
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate([{"role": "user", "content": "hi"}])
        
        # Assert
        assert result == "Hello World"
        mock_instance.invoke.assert_called_once()

def test_GenerateJson_ShouldReturnParsedDict_WhenValidInputProvided(mock_chat_openai):
    """Verify generate_json method returns parsed dict."""
    # Arrange
    mock_instance = mock_chat_openai.return_value
    mock_response = MagicMock()
    mock_response.content = '{"key": "value"}'
    
    # Mocking for bound json model
    mock_bound = MagicMock()
    mock_bound.invoke.return_value = mock_response
    mock_instance.bind.return_value = mock_bound
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}])
        
        # Assert
        assert result == {"key": "value"}
        mock_instance.bind.assert_called_once_with(response_format={"type": "json_object"})
        mock_bound.invoke.assert_called_once()

def test_GenerateJson_ShouldRaiseValueError_WhenResponseIsInvalidJson(mock_chat_openai):
    """Verify that invalid JSON raises ValueError."""
    # Arrange
    mock_instance = mock_chat_openai.return_value
    mock_response = MagicMock()
    mock_response.content = 'Invalid JSON'
    
    # Mocking for bound json model
    mock_bound = MagicMock()
    mock_bound.invoke.return_value = mock_response
    mock_instance.bind.return_value = mock_bound
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Model returned invalid JSON"):
            client.generate_json([{"role": "user", "content": "hi"}])

def test_GenerateJson_ShouldUseStructuredOutput_WhenResponseFormatProvided(mock_chat_openai):
    """Verify that with_structured_output is used for structured outputs."""
    # Arrange
    mock_instance = mock_chat_openai.return_value
    mock_structured = MagicMock()
    
    mock_pydantic = MagicMock()
    mock_pydantic.model_dump.return_value = {"key": "structured"}
    mock_structured.invoke.return_value = mock_pydantic
    mock_instance.with_structured_output.return_value = mock_structured
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}], response_format=MagicMock())
        
        # Assert
        assert result == {"key": "structured"}
        mock_instance.with_structured_output.assert_called_once()
        mock_structured.invoke.assert_called_once()

def test_GenerateJson_ShouldFallbackToDict_WhenParsedIsDict(mock_chat_openai):
    """Verify fallback to direct dict return when parsed is a dict."""
    # Arrange
    mock_instance = mock_chat_openai.return_value
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = {"key": "fallback"}
    mock_instance.with_structured_output.return_value = mock_structured
    
    with patch("os.getenv", return_value="fake_key"):
        client = LLMApiClient()
        
        # Act
        result = client.generate_json([{"role": "user", "content": "hi"}], response_format=MagicMock())
        
        # Assert
        assert result == {"key": "fallback"}
