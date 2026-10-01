import sqlite3
import time
import lightgbm as lgb
import numpy as np
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import FEATURE_COLUMNS

DB_PATH = os.path.join(REPO_ROOT, "database", "eurusd-data.db")
AGGREGATION_DATA_TABLE = "aggregationData"
TRADES_TABLE = "trades"

# Resolve model paths relative to this script file so PM2/current working dir won't break them
MODEL_LONG_ATR_PATH = os.path.join(SCRIPT_DIR, "model_long_atr.txt")
MODEL_SHORT_ATR_PATH = os.path.join(SCRIPT_DIR, "model_short_atr.txt")

# Fail early with a clear message if model files are missing
if not os.path.exists(MODEL_LONG_ATR_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_LONG_ATR_PATH}")
if not os.path.exists(MODEL_SHORT_ATR_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_SHORT_ATR_PATH}")

T_LONG_ATR = 0.20
T_SHORT_ATR = 0.20

# ============================================================
# Load models
# ============================================================
model_long = lgb.Booster(model_file=MODEL_LONG_ATR_PATH)
model_short = lgb.Booster(model_file=MODEL_SHORT_ATR_PATH)

# ============================================================
# Ensemble ATR-only
# ============================================================
def ensemble_signal(x):
    pLong = float(model_long.predict(x)[0])
    pShort = float(model_short.predict(x)[0])

    long_sig = pLong > T_LONG_ATR
    short_sig = pShort > T_SHORT_ATR

    if long_sig and not short_sig:
        return 1, pLong, pShort
    if short_sig and not long_sig:
        return -1, pLong, pShort
    if long_sig and short_sig:
        return (1 if pLong > pShort else -1), pLong, pShort

    return 0, pLong, pShort

# ============================================================
# Save trade
# ============================================================
def save_trade(trade):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    currentDate = datetime.now(timezone.utc)
    #day = currentDate.day
    month = currentDate.month
    hour = currentDate.hour
    weekday = currentDate.weekday()

    cur.execute(f"""
        INSERT INTO {TRADES_TABLE} (
            mode, entry_time, created_at, exit_time, direction, entry_price, exit_price,
            pnl, reason, pLongAtr, pShortAtr, entry_hour, entry_weekday, entry_month
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "live",
        trade["entry_time"],
        currentDate.isoformat(),
        None,
        trade["direction"],
        trade["entry_price"],
        None,
        None,
        "OPEN",
        trade["pLongAtr"],
        trade["pShortAtr"],
        hour,
        weekday,
        month
    ))

    conn.commit()
    conn.close()

# ============================================================
# Main loop
# ============================================================
def main():

    #last_id = None
    last_id = -1

    while True:
        print("Signal Engine avviato. In ascolto dei nuovi dati live...")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(f"SELECT id FROM {AGGREGATION_DATA_TABLE} ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()

        if row:
            current_id = row[0]

            #if last_id is None:
            #    last_id = current_id

            if current_id > last_id:
                # New live candle available
                cur.execute(f"SELECT * FROM {AGGREGATION_DATA_TABLE} WHERE id = ?", (current_id,))
                data = cur.fetchone()
                
                # Convert to dict
                columns = [col[0] for col in cur.description]
                row_dict = dict(zip(columns, data))

                #print(f"Nuovo dato live disponibile ----> {json.dumps(row_dict, ensure_ascii=False)}")

                # Build feature vector
                x = np.array([[row_dict[col] for col in FEATURE_COLUMNS]])

                # Predict
                signal, pLong, pShort = ensemble_signal(x)

                if signal != 0:
                    trade = {
                        "entry_time": row_dict["timestamp_m5"],
                        "direction": signal,
                        "entry_price": row_dict["close_m5"],
                        "pLongAtr": pLong,
                        "pShortAtr": pShort
                    }

                    save_trade(trade)
                    print(f"[{datetime.now()}] Segnale generato: {signal}, prezzo={trade['entry_price']}")

                last_id = current_id

        conn.close()
        print("Signal Engine terminato!")
        time.sleep(10)  # Poll every 10 seconds

if __name__ == "__main__":
    main()
