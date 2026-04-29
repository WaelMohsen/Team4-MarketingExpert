import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.shared.utils.prompt_loader import PromptLoader

def test_FromModuleDir_ShouldReturnPromptLoader_WhenCalled():
    """Verify that PromptLoader can be initialized from the module directory."""
    # Act
    with patch("src.shared.utils.prompt_loader.Path") as mock_path:
        # Mocking __file__ path logic
        mock_path(__file__).resolve.return_value.parent.return_value = Path("/mock/shared/utils")
        
        loader = PromptLoader.from_module_dir()
        
        # Assert
        assert isinstance(loader, PromptLoader)

def test_LoadPromptText_ShouldReturnContent_WhenFileExists():
    """Verify loading text from an existing file."""
    # Arrange
    mock_dir = Path("/mock/prompts")
    loader = PromptLoader(prompts_dir=mock_dir)
    content = "Mock prompt content"
    
    # Act
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.open", mock_open(read_data=content)) as mock_file:
            result = loader.load_prompt_text("test.txt")
            
            # Assert
            assert result == content
            # Ensure it tried to open the correct path
            mock_file.assert_called_once_with("r", encoding="utf-8")

def test_LoadPromptText_ShouldRaiseFileNotFoundError_WhenFileDoesNotExist():
    """Verify that FileNotFoundError is raised for missing files."""
    # Arrange
    loader = PromptLoader(prompts_dir=Path("/mock/prompts"))
    
    # Act & Assert
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            loader.load_prompt_text("missing.txt")
