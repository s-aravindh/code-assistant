"""Database setup and helpers for SQLite storage."""

import os
from pathlib import Path

from agno.db.sqlite import SqliteDb


def get_default_db_path() -> str:
    """Get the default database path."""
    if os.name == "posix":
        data_dir = Path.home() / ".local" / "share" / "mcc"
    else:
        data_dir = Path.home() / "AppData" / "Local" / "mcc"

    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "mcc.db")


def create_database(db_path: str | None = None) -> SqliteDb:
    """Create and initialize the database."""
    return SqliteDb(db_file=db_path or get_default_db_path())
