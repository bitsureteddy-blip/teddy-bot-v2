"""Dispatcher composition boundary.

Kept intentionally thin in this structural migration so existing startup logic
continues to run from the root `main.py` without behavioral changes.
"""


def build_dispatcher(application):
    """Return the provided Telegram application unchanged.

    Future migrations can move handler registration here once tests cover the
    current behavior.
    """
    return application
