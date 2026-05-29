"""Paper trading service boundary backed by the existing paper trader."""
from app.core.paper_trader import PaperTrader

__all__ = ["PaperTrader"]
