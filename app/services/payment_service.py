"""Payment service boundary backed by existing payment helpers."""
from app.external.payments import generate_binance_payment

__all__ = ["generate_binance_payment"]
