"""Simple session-based logging."""

import logging
from datetime import datetime
from pathlib import Path


def create_logger(
    session_id: str,
    log_dir: Path | str | None = None,
    project_path: Path | str | None = None,
    level: str = "INFO",
) -> logging.Logger:
    """Create a session logger.

    Args:
        session_id: Session identifier
        log_dir: Custom log directory (takes precedence)
        project_path: Project path (uses project_path/mcc_logs)
        level: Log level (DEBUG, INFO, WARNING, ERROR)

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

    # File handler
    log_file = log_path / f"{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    logger.addHandler(handler)

    logger.info(f"Session started: {log_file}")
    return logger
