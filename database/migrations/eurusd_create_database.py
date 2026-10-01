from pathlib import Path
import sqlite3

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "database" / "eurusd-data.db"

def create_db():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Tabella trades
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL CHECK(mode IN ('live', 'backtest')),
            entry_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            exit_time TEXT,
            direction INTEGER NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            pnl REAL,
            reason TEXT,
            pLongAtr REAL,
            pShortAtr REAL,
            entry_hour INTEGER,
            entry_weekday INTEGER,
            entry_month INTEGER
        );
    """)

    # Indici
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trades_mode ON trades(mode);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);")

    conn.commit()
    conn.close()
    print("Database creato con successo.")

if __name__ == "__main__":
    create_db()
