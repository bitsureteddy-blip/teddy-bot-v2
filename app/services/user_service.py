"""User service boundary.

This module intentionally delegates to the existing legacy UserManager so the
project can adopt the new architecture without changing business behavior.
"""
from legacy.user_manager import UserManager

__all__ = ["UserManager"]
