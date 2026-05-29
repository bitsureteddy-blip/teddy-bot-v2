"""Alert service boundary backed by the legacy AlertManager."""
from legacy.alert_manager import AlertManager

__all__ = ["AlertManager"]
