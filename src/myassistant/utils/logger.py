"""Session-based logging with rotation support."""

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


def create_logger(
    session_id: str,
    log_dir: Path | str | None = None,
    project_path: Path | str | None = None,
    level: str = "INFO",
    max_size_mb: int = 10,
    backup_count: int = 5,
) -> logging.Logger:
    """Create a session logger with optional rotation.

    Args:
        session_id: Session identifier
        log_dir: Custom log directory (takes precedence)
        project_path: Project path (uses project_path/mcc_logs)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        max_size_mb: Maximum log file size in MB before rotation (default: 10)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured logger instance
    """
    # Resolve log directory
    if log_dir:
        log_path = Path(log_dir).resolve()
    elif project_path:
        log_path = Path(project_path).resolve() / "mcc_logs"
    else:
        log_path = Path.cwd() / "mcc_logs"

    log_path.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(f"mcc_{session_id[:8]}")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    # Log file path
    log_file = log_path / f"{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Use RotatingFileHandler for automatic rotation
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count,
        encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    logger.addHandler(handler)

    logger.info(f"Session started: {log_file}")
    logger.debug(f"Log rotation: max {max_size_mb}MB, {backup_count} backups")
    return logger


