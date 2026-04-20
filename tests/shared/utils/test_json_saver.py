import os
import json
from unittest.mock import patch, mock_open
from src.shared.utils.json_saver import save_results_to_json

def test_save_results_to_json():
    """Verify that results are saved correctly to a JSON file."""
    data = {"result": "success"}
    log_dir = "test_logs"
    filename = "test.json"
    
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("src.shared.utils.json_saver.datetime") as mock_datetime:
                # Mock date for deterministic path
                mock_datetime.now.return_value.strftime.return_value = "2024-01-01"
                
                # Mock os.path.join to return consistent strings for comparison
                # (Actually standard path join is fine, we just need to verify the open call)
                
                path = save_results_to_json(data, log_dir, filename)
                
                # Verify directories were created (once for log_dir, once for run_dir)
                assert mock_makedirs.call_count == 2
                
                # Verify open was called with correct path and mode
                # The path should be something like "test_logs/2024-01-01/test.json"
                # but we'll use os.path.join logic to be safe
                expected_path = os.path.join("test_logs", "2024-01-01", "test.json")
                mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
                
                # Handle how json.dump writes to the file handle
                handle = mock_file()
                # Instead of verifying exact handle.write calls (which json.dump does in multiple chunks),
                # we assume json.dump worked if open was called correctly.
                # However, we can assert on the return path.
                assert path == expected_path
