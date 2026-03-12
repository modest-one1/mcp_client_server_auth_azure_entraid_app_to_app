import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
load_dotenv()

def setup_logger(
    log_file: str = "./app.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
    fmt: str = "%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s"
) -> logging.Logger:
    """
    Setup a rotating file logger that captures datetime, filename, function name,
    log level, and message.

    Args:
        name (str): Logger name (usually __name__).
        log_file (str): Path to the log file.
        level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes (int): Maximum file size before rotation (in bytes).
        backup_count (int): Number of backup files to keep.
        fmt (str): Log format.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Prevent adding handlers multiple times if logger is reused
    if not logger.handlers:
        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(fmt))

        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(fmt))

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger



def _get_env_var(name, default=None, cast_type=str):
    value = os.environ.get(name, default)
    if value is not None and cast_type is not str:
        try:
            value = cast_type(value)
        except Exception:
            value = default
    return value

logger = setup_logger(
    log_file=_get_env_var("LOG_FILENAME", "./app.log"),
    level=logging.INFO,
    max_bytes=_get_env_var("LOG_SIZE", 5 * 1024 * 1024, int),
    backup_count=_get_env_var("LOG_BACKUP_COUNT", 5, int),
    fmt=_get_env_var("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s")
)