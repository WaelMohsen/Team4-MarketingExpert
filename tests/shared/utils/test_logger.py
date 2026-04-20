import logging
from unittest.mock import patch, MagicMock
from src.shared.utils.logger import setup_logging

def test_setup_logging_initialization():
    """Verify that setup_logging configures the logger correctly."""
    with patch("pathlib.Path") as mock_path:
        # Configure mock path for BASE_LOG_DIR / "logs"
        mock_log_dir = MagicMock()
        mock_path.return_value.resolve.return_value.parent.parent.__truediv__.return_value = mock_log_dir
        
        with patch("logging.basicConfig") as mock_basic_config:
            with patch("logging.FileHandler"):
                with patch("logging.StreamHandler"):
                    logger = setup_logging("test_module")
            
            # Verify directories were created
            mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify basicConfig was called
            mock_basic_config.assert_called_once()
            args, kwargs = mock_basic_config.call_args
            assert kwargs["level"] == logging.INFO
            assert "handlers" in kwargs
            
            # Verify logger instance
            assert logger.name == "test_module"
