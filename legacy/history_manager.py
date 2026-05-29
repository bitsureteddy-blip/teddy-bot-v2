"""
Gestionnaire d'historique des signaux pour Bitsure Teddy.
Stockage SQLite uniquement.
"""

import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HistoryManager:
    _instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # =========================================================
    # HELPERS
    # =========================================================

    def _row_to_dict(self, row) -> Dict:
        if not row:
            return None

        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "direction": row["direction"],
            "entry_price": row["entry_price"],
            "timeframe": row["timeframe"] if "timeframe" in row.keys() else "1h",
            "type": row["type"] if "type" in row.keys() else "analyse",
            "score": row["score"],
            "timestamp": (
                datetime.utcfromtimestamp(row["created_at"]).isoformat()
                if row["created_at"]
                else ""
            ),
            "closed_timestamp": (
                datetime.utcfromtimestamp(row["closed_at"]).isoformat()
                if "closed_at" in row.keys() and row["closed_at"]
                else None
            ),
            "status": row["status"],
            "sl": row["sl"],
            "tp": row["tp"],
            "result_price": (
                row["result_price"]
                if "result_price" in row.keys()
                else None
            ),
            "result_pct": row["result_pct"],
        }

    # =========================================================
    # AJOUT
    # =========================================================

    def add_signal(
        self,
        symbol: str,
        direction: str,
        price: float,
        timeframe: str,
        signal_type: str = "analyse",
        score: int = 0,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> str:

        signal_id = hashlib.md5(
            f"{symbol}{direction}{price}{timeframe}{time.time()}".encode()
        ).hexdigest()[:8]

        now = time.time()

        from database import get_db

        conn = get_db()

        conn.execute(
            """
            INSERT OR REPLACE INTO signals (
                id,
                symbol,
                direction,
                entry_price,
                sl,
                tp,
                score,
                status,
                result_pct,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                symbol.upper(),
                direction.upper(),
                price,
                sl,
                tp,
                score,
                "pending",
                None,
                now,
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"✅ Signal ajouté: {signal_id}")

        return signal_id

    # =========================================================
    # LECTURE
    # =========================================================

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        from database import get_db

        conn = get_db()

        rows = conn.execute(
            """
            SELECT * FROM signals
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        conn.close()

        return [self._row_to_dict(r) for r in rows]

    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        from database import get_db

        conn = get_db()

        row = conn.execute(
            "SELECT * FROM signals WHERE id=?",
            (signal_id,),
        ).fetchone()

        conn.close()

        return self._row_to_dict(row) if row else None

    # =========================================================
    # MISE À JOUR
    # =========================================================

    def update_signal_status(
        self,
        signal_id: str,
        status: str,
        result_pct: float,
        result_price: Optional[float] = None,
    ) -> Optional[Dict]:
        """
        Met à jour le statut final d'un signal.
        """

        from database import get_db

        # Clamp sécurité
        result_pct = max(-100, min(400, result_pct))

        conn = get_db()

        conn.execute(
            """
            UPDATE signals
            SET
                status=?,
                result_pct=?,
                result_price=?,
                closed_at=?
            WHERE id=?
            """,
            (
                status,
                result_pct,
                result_price,
                time.time(),
                signal_id,
            ),
        )

        conn.commit()

        row = conn.execute(
            "SELECT * FROM signals WHERE id=?",
            (signal_id,),
        ).fetchone()

        conn.close()

        logger.info(
            f"✅ Signal {signal_id} clôturé: "
            f"{status} ({result_pct}%)"
        )

        return self._row_to_dict(row) if row else None

    def update_signal_result(
        self,
        signal_id: str,
        current_price: float,
    ) -> Optional[str]:
        """
        Vérifie si TP ou SL est touché.
        """

        signal = self.get_signal_by_id(signal_id)

        if not signal:
            logger.warning(f"❌ Signal introuvable: {signal_id}")
            return None

        if signal["status"] != "pending":
            return None

        entry = signal["entry_price"]
        sl = signal.get("sl")
        tp = signal.get("tp")
        direction = signal["direction"]

        # =====================================================
        # BUY
        # =====================================================

        if direction == "BUY":

            # TAKE PROFIT
            if tp and current_price >= tp:

                result_pct = round(
                    ((current_price - entry) / entry) * 100,
                    4,
                )

                self.update_signal_status(
                    signal_id,
                    "win",
                    result_pct,
                    current_price,
                )

                return "win"

            # STOP LOSS
            elif sl and current_price <= sl:

                result_pct = round(
                    ((current_price - entry) / entry) * 100,
                    4,
                )

                self.update_signal_status(
                    signal_id,
                    "loss",
                    result_pct,
                    current_price,
                )

                return "loss"

        # =====================================================
        # SELL
        # =====================================================

        elif direction == "SELL":

            # TAKE PROFIT
            if tp and current_price <= tp:

                result_pct = round(
                    ((entry - current_price) / entry) * 100,
                    4,
                )

                self.update_signal_status(
                    signal_id,
                    "win",
                    result_pct,
                    current_price,
                )

                return "win"

            # STOP LOSS
            elif sl and current_price >= sl:

                result_pct = round(
                    ((entry - current_price) / entry) * 100,
                    4,
                )

                self.update_signal_status(
                    signal_id,
                    "loss",
                    result_pct,
                    current_price,
                )

                return "loss"

        return None

    # =========================================================
    # NETTOYAGE
    # =========================================================

    def clear_all_signals(self):
        from database import get_db

        conn = get_db()

        conn.execute("DELETE FROM signals")

        conn.commit()
        conn.close()

        logger.info("✅ Tous les signaux ont été effacés")

    def clear_old_signals(self, days: int = 30):
        from database import get_db

        cutoff = time.time() - (days * 86400)

        conn = get_db()

        conn.execute(
            "DELETE FROM signals WHERE created_at < ?",
            (cutoff,),
        )

        conn.commit()
        conn.close()

        logger.info(
            f"✅ Signaux de plus de {days} jours supprimés"
        )