"""User repository boundary backed by the current database helpers."""
from app.db.database import get_db

__all__ = ["get_db"]
