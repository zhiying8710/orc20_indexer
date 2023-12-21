import os
from loguru import logger


def setup_logging():
    """
    Set up logging configuration.

    This function creates a directory for logs if it doesn't exist,
    and configures the loguru logger to write logs to a file with rotation
    and retention settings.

    Args:
        None

    Returns:
        None
    """
    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)

    log_file_path = os.path.join(logs_directory, "orc20_indexer.log")

    logger.add(
        log_file_path,
        rotation="100 MB",
        retention="30 days",
        level="INFO",
    )
