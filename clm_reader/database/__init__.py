"""Module de base de données pour CLM Reader."""

from .db_manager import Database, get_default_db_path

__all__ = ["Database", "get_default_db_path"]
