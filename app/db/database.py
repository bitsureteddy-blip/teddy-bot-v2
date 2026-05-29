import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bitsure.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            role TEXT DEFAULT 'free',
            lang TEXT DEFAULT 'en',
            timeframe TEXT DEFAULT '1h',
            risk TEXT DEFAULT 'medium',
            terms_accepted INTEGER DEFAULT 0,
            trial_start REAL,
            created_at REAL
        );

        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            sl REAL,
            tp REAL,
            score INTEGER,
            status TEXT DEFAULT 'pending',
            result_pct REAL,
            created_at REAL,
            closed_at REAL
        );

        CREATE TABLE IF NOT EXISTS paper_positions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            symbol TEXT,
            entry_price REAL,
            sl REAL,
            tp REAL,
            qty REAL,
            current_price REAL,
            pnl_usdt REAL,
            pnl_pct REAL,
            status TEXT DEFAULT 'open',
            exit_reason TEXT,
            opened_at REAL,
            closed_at REAL,
            peak_price REAL
        );

        CREATE TABLE IF NOT EXISTS paper_capitals (
            user_id INTEGER PRIMARY KEY,
            capital REAL DEFAULT 10000
        );

        CREATE TABLE IF NOT EXISTS watchlists (
            user_id INTEGER,
            symbol TEXT,
            PRIMARY KEY (user_id, symbol)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            condition TEXT,
            price REAL,
            triggered INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()