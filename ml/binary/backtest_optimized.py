import pandas as pd
import numpy as np
import lightgbm as lgb
import time
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import FEATURE_COLUMNS, add_derived_features

# ============================================================
# CONFIG
# ============================================================
CSV_TEST = ML_DIR / "eurusd_test.csv"

MODEL_LONG_ATR_PATH = SCRIPT_DIR / "model_long_atr.txt"
MODEL_SHORT_ATR_PATH = SCRIPT_DIR / "model_short_atr.txt"

# Threshold ottimali trovati nei test
T_LONG_ATR = 0.20
T_SHORT_ATR = 0.20

# Parametri backtest
N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0

# ============================================================
# CARICAMENTO MODELLI
# ============================================================
model_long_atr = lgb.Booster(model_file=MODEL_LONG_ATR_PATH)
model_short_atr = lgb.Booster(model_file=MODEL_SHORT_ATR_PATH)

# ============================================================
# ENSEMBLE ATR‑ONLY
# ============================================================
def ensemble_atr_signal(x_row):
    pLongAtr = float(model_long_atr.predict(x_row)[0])
    pShortAtr = float(model_short_atr.predict(x_row)[0])

    long_signal = pLongAtr > T_LONG_ATR
    short_signal = pShortAtr > T_SHORT_ATR

    # BUY
    if long_signal and not short_signal:
        return 1, pLongAtr, pShortAtr

    # SELL
    if short_signal and not long_signal:
        return -1, pLongAtr, pShortAtr

    # Conflitto → vince il più forte
    if long_signal and short_signal:
        if pLongAtr > pShortAtr:
            return 1, pLongAtr, pShortAtr
        else:
            return -1, pLongAtr, pShortAtr

    # HOLD
    return 0, pLongAtr, pShortAtr

# ============================================================
# BACKTEST ENGINE (OTTIMIZZATO)
# ============================================================
def run_backtest(df):
    equity = 0.0
    trades = []

    prices = df["close_m5"].values
    atr = df["atr14_m5"].values
    highs = df["high_m5"].values
    lows = df["low_m5"].values

    i = 0
    n = len(df)

    while i < n:
        x = df.iloc[i:i+1][FEATURE_COLUMNS].values
        signal, pLongAtr, pShortAtr = ensemble_atr_signal(x)

        if signal == 0:
            i += 1
            continue

        entry_price = prices[i]
        atr_val = atr[i]
        sl = ATR_SL_MULT * atr_val
        tp = ATR_TP_MULT * atr_val

        direction = signal
        entry_index = i

        exit_price = None
        exit_reason = None
        exit_index = i + 1

        # Ricerca efficiente dell'exit usando vettorizzazione
        j = i + 1
        max_j = min(i + N_MAX_BARS + 1, n)
        
        if direction == 1:  # BUY
            high_slice = highs[j:max_j]
            low_slice = lows[j:max_j]
            
            # TP hit
            tp_hits = np.where(high_slice >= entry_price + tp)[0]
            if len(tp_hits) > 0:
                exit_index = j + tp_hits[0]
                exit_price = entry_price + tp
                exit_reason = "TP"
            else:
                # SL hit
                sl_hits = np.where(low_slice <= entry_price - sl)[0]
                if len(sl_hits) > 0:
                    exit_index = j + sl_hits[0]
                    exit_price = entry_price - sl
                    exit_reason = "SL"
                else:
                    exit_index = max_j - 1
                    exit_price = prices[min(max_j - 1, n - 1)]
                    exit_reason = "TIME"
        else:  # SELL
            high_slice = highs[j:max_j]
            low_slice = lows[j:max_j]
            
            # TP hit
            tp_hits = np.where(low_slice <= entry_price - tp)[0]
            if len(tp_hits) > 0:
                exit_index = j + tp_hits[0]
                exit_price = entry_price - tp
                exit_reason = "TP"
            else:
                # SL hit
                sl_hits = np.where(high_slice >= entry_price + sl)[0]
                if len(sl_hits) > 0:
                    exit_index = j + sl_hits[0]
                    exit_price = entry_price + sl
                    exit_reason = "SL"
                else:
                    exit_index = max_j - 1
                    exit_price = prices[min(max_j - 1, n - 1)]
                    exit_reason = "TIME"

        pnl = exit_price - entry_price if direction == 1 else entry_price - exit_price
        equity += pnl

        exit_idx = min(exit_index, n - 1)

        trades.append({
            "entry_index": entry_index,
            "exit_index": exit_idx,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": exit_reason,
            "entry_time": df["timestamp_m5"].iloc[entry_index],
            "exit_time": df["timestamp_m5"].iloc[exit_idx],
            "entry_year": df["year"].iloc[entry_index],
            "entry_month": df["month"].iloc[entry_index],
            "entry_hour": df["hour"].iloc[entry_index],
            "pLongAtr": pLongAtr,
            "pShortAtr": pShortAtr
        })

        i = exit_idx + 1

    return equity, trades

# ============================================================
# ANALISI TRADE
# ============================================================
def analyze_trades(trades):
    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]

    total_pnl = pnls.sum()
    winrate = len(wins) / len(trades) if len(trades) > 0 else 0
    avg_win = wins.mean() if len(wins) else 0
    avg_loss = losses.mean() if len(losses) else 0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else np.inf

    equity_curve = pnls.cumsum()
    peak = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - peak
    max_dd = drawdown.min() if len(drawdown) > 0 else 0

    return {
        "num_trades": len(trades),
        "total_pnl": total_pnl,
        "winrate": winrate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "equity_curve": equity_curve
    }

# ============================================================
# ANALISI PER ANNO / MESE / ORA
# ============================================================
def analyze_by_group(trades, key):
    df = pd.DataFrame(trades)
    groups = df.groupby(key)

    rows = []
    for k, g in groups:
        pnls = g["pnl"].values
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        profit_factor = wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else np.inf
        winrate = len(wins) / len(pnls)
        avg_pnl = pnls.mean()

        rows.append({
            key: k,
            "num_trades": len(pnls),
            "winrate": winrate,
            "profit_factor": profit_factor,
            "avg_pnl": avg_pnl
        })

    return pd.DataFrame(rows).sort_values(key)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    start_time = time.time()
    
    print("Loading data...")
    df = add_derived_features(pd.read_csv(CSV_TEST))
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"])
    df["year"] = df["timestamp_m5"].dt.year
    df["month"] = df["timestamp_m5"].dt.month
    df["hour"] = df["timestamp_m5"].dt.hour

    print(f"Data loaded: {len(df)} rows")
    print("Running backtest...")
    equity, trades = run_backtest(df)
    print(f"Backtest completed: {len(trades)} trades")
    
    stats = analyze_trades(trades)

    print("\n=== RISULTATI BACKTEST ENSEMBLE ATR ===")
    print("Numero trade:", stats["num_trades"])
    print("PNL totale:", stats["total_pnl"])
    print("Winrate:", stats["winrate"])
    print("Profit factor:", stats["profit_factor"])
    print("Max drawdown:", stats["max_drawdown"])

    print("\n=== ANALISI PER ANNO ===")
    print(analyze_by_group(trades, "entry_year"))

    print("\n=== ANALISI PER MESE ===")
    print(analyze_by_group(trades, "entry_month"))

    print("\n=== ANALISI PER ORA ===")
    print(analyze_by_group(trades, "entry_hour"))
    
    # Calcolo del tempo totale
    end_time = time.time()
    elapsed_seconds = int(end_time - start_time)
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    print(f"\n⏱️  Tempo totale di esecuzione: {minutes}m {seconds}s")