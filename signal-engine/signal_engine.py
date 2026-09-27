import json
import sqlite3
import time
import lightgbm as lgb
import numpy as np
import os
from datetime import datetime, timezone

DB_PATH = "C:\\Repos\\LiveMarketDataApp\\database\\eurusd-data.db"
AGGREGATION_DATA_TABLE = "aggregationData"
TRADES_TABLE = "trades"

# Resolve model paths relative to this script file so PM2/current working dir won't break them
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_LONG_ATR_PATH = os.path.join(SCRIPT_DIR, "model_long_atr.txt")
MODEL_SHORT_ATR_PATH = os.path.join(SCRIPT_DIR, "model_short_atr.txt")

# Fail early with a clear message if model files are missing
if not os.path.exists(MODEL_LONG_ATR_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_LONG_ATR_PATH}")
if not os.path.exists(MODEL_SHORT_ATR_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_SHORT_ATR_PATH}")

FEATURE_COLUMNS = [
    "open_m5","close_m5","high_m5","low_m5","volume_m5",
    "sma20_m5","sma50_m5","ema20_m5","ema50_m5","ema100_m5","ema200_m5",
    "bbands20_m5","rsi14_m5","atr14_m5","macdNorm_m5","slopeEma_m5",
    "distanceEma_m5","roc_m5","stoch_m5","obv_m5","volumeZScore_m5",
    "volumeAtrRatio_m5","fvgBullish_m5","fvgBearish_m5","fvgSize_m5",
    "fvgSizeAtrNorm_m5","bodySizePerc_m5","upperWickPerc_m5",
    "lowerWickPerc_m5","rangeExp_m5","logReturn_m5","rollingVolatility_m5",
    "rollingVolatilityAtrNorm_m5","rollingVolatilitySlope_m5",
    "sma20_m15","sma50_m15","ema20_m15","ema50_m15","ema100_m15",
    "ema200_m15","bbands20_m15","rsi14_m15","atr14_m15","macdNorm_m15",
    "slopeEma_m15","distanceEma_m15","roc_m15","stoch_m15","obv_m15",
    "volumeZScore_m15","volumeAtrRatio_m15","fvgBullish_m15",
    "fvgBearish_m15","fvgSize_m15","fvgSizeAtrNorm_m15","bodySizePerc_m15",
    "upperWickPerc_m15","lowerWickPerc_m15","rangeExp_m15","logReturn_m15",
    "rollingVolatility_m15","rollingVolatilityAtrNorm_m15",
    "rollingVolatilitySlope_m15",
    "sma20_h1","sma50_h1","ema20_h1","ema50_h1","ema100_h1","ema200_h1",
    "bbands20_h1","rsi14_h1","atr14_h1","macdNorm_h1","slopeEma_h1",
    "distanceEma_h1","roc_h1","stoch_h1","obv_h1","volumeZScore_h1",
    "volumeAtrRatio_h1","fvgBullish_h1","fvgBearish_h1","fvgSize_h1",
    "fvgSizeAtrNorm_h1","bodySizePerc_h1","upperWickPerc_h1",
    "lowerWickPerc_h1","rangeExp_h1","logReturn_h1","rollingVolatility_h1",
    "rollingVolatilityAtrNorm_h1","rollingVolatilitySlope_h1"
]

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
