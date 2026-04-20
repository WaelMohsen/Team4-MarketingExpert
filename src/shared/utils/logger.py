import os
import logging
from datetime import datetime

def setup_logging(file_name:str, module_name: str=__name__):
    """
    Configures application-wide logging with a timestamped run directory.
    Args:
        basebase_log_dir_dir (str): Base directory for logs.
        module_name (str): name to create a logger scoped to the current module so logs are traceable, structured, and scalable
    Returns:
        str: The created run directory path.
    """
    # Base logs directory
    from pathlib import Path

    BASE_LOG_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_LOG_DIR / "logs"
    # Create directories
    LOG_DIR.mkdir(parents=True, exist_ok=True)


    # Log file inside the run directory
    log_file = LOG_DIR / file_name
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        # Define log message format: timestamp | level | logger name | message
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            # Write logs to a file with UTF-8 encoding
            logging.FileHandler(log_file, encoding="utf-8"),
            # Print logs to the console 
            logging.StreamHandler()
        ]
    )
    # Create a logger instance named after the current module (for organized logging)
    # It takes the name of module (class name)
    logger = logging.getLogger(module_name) 
    # Optional: log the run directory for traceability
    logging.info(f"Logging initialized.")
    return logger
    
