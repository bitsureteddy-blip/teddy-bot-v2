import hashlib
import time
from config import BINANCE_ID
from i18n import get_text

def generate_binance_payment(user_id: int, lang: str) -> tuple:
    ident = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8].upper()
    text = get_text(lang, "binance_payment_info", amount="19.99", binance_id=BINANCE_ID, memo=ident)
    return ident, text
