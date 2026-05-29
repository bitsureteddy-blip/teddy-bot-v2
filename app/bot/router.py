"""Telegram handler routing helpers for the clean architecture layer.

The live bot still uses the root `main.py` entrypoint during this migration.
These imports expose the relocated handlers from their new package location.
"""
from app.bot.handlers.commands.bot_handlers import *
from app.bot.handlers.commands.admin_handlers import *
