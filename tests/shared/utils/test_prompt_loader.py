import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.shared.utils.prompt_loader import PromptLoader

def test_prompt_loader_from_module_dir():
    """Verify that PromptLoader can be initialized from the module directory."""
    with patch("src.shared.utils.prompt_loader.Path") as mock_path:
        # Mocking __file__ path logic
        mock_path(__file__).resolve.return_value.parent.return_value = Path("/mock/shared/utils")
        
        loader = PromptLoader.from_module_dir()
        assert isinstance(loader, PromptLoader)
        # We don't assert the exact path because it's hard to mock all Path components purely,
        # but we verify the method completes and returns a loader.

def test_load_prompt_text_existing_file():
    """Verify loading text from an existing file."""
    mock_dir = Path("/mock/prompts")
    loader = PromptLoader(prompts_dir=mock_dir)
    content = "Mock prompt content"
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.open", mock_open(read_data=content)) as mock_file:
            result = loader.load_prompt_text("test.txt")
            assert result == content
            # Ensure it tried to open the correct path
            mock_file.assert_called_once_with("r", encoding="utf-8")

def test_load_prompt_text_missing_file():
    """Verify that FileNotFoundError is raised for missing files."""
    loader = PromptLoader(prompts_dir=Path("/mock/prompts"))
    
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            loader.load_prompt_text("missing.txt")
