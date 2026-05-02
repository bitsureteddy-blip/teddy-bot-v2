import hashlib
import time
from config import BINANCE_USDC_ADDRESS
from i18n import get_text


def generate_binance_payment(user_id: int, lang: str):
    ident = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8].upper()
    amount = "19.99 USDC"
    text = get_text(lang, "binance_payment_info", amount=amount, address=BINANCE_USDC_ADDRESS, memo=ident)
    return ident, text
