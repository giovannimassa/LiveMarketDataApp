import pandas as pd
import numpy as np
import lightgbm as lgb
from collections import Counter
from itertools import product
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import FEATURE_COLUMNS

# ============================================================
# CONFIG
# ============================================================
MODEL_PATH = "eurusd_lgbm.txt"
CSV_TEST   = "eurusd_test.csv"

T_BUY  = 0.30
T_SELL = 0.30

N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0

# ============================================================
# THRESHOLDING
# ============================================================
def apply_thresholding(probabilities, t_buy=T_BUY, t_sell=T_SELL):
    preds = []
    for p in probabilities:
        p_sell = p[0]
        p_hold = p[1]
        p_buy  = p[2]

        if p_buy >= t_buy and p_buy > p_sell:
            preds.append(1)
            continue

        if p_sell >= t_sell and p_sell > p_buy:
            preds.append(-1)
            continue

        preds.append(0)

    return np.array(preds)

# ============================================================
# BACKTEST ENGINE
# ============================================================
def run_backtest(df, signals):
    equity = 0.0
    trades = []

    prices = df["close_m5"].values
    atr    = df["atr14_m5"].values

    i = 0
    n = len(df)

    while i < n:
        sig = signals[i]

        if sig == 0:
            i += 1
            continue

        entry_price = prices[i]
        atr_val     = atr[i]
        sl = ATR_SL_MULT * atr_val
        tp = ATR_TP_MULT * atr_val

        direction = sig
        entry_index = i

        exit_price = None
        exit_reason = None

        j = i + 1
        while j < n and j - i <= N_MAX_BARS:
            high = df["high_m5"].iloc[j]
            low  = df["low_m5"].iloc[j]

            if direction == 1:
                if high >= entry_price + tp:
                    exit_price = entry_price + tp
                    exit_reason = "TP"
                    break
                if low <= entry_price - sl:
                    exit_price = entry_price - sl
                    exit_reason = "SL"
                    break
            else:
                if low <= entry_price - tp:
                    exit_price = entry_price - tp
                    exit_reason = "TP"
                    break
                if high >= entry_price + sl:
                    exit_price = entry_price + sl
                    exit_reason = "SL"
                    break

            j += 1

        if exit_price is None:
            exit_price = prices[min(j, n - 1)]
            exit_reason = "TIME"

        # Limita j ai limiti del dataframe
        j = min(j, n - 1)

        pnl = exit_price - entry_price if direction == 1 else entry_price - exit_price
        equity += pnl

        trades.append({
            "entry_index": entry_index,
            "exit_index": j,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": exit_reason,
            "entry_time": df["timestamp_m5"].iloc[entry_index],
            "exit_time": df["timestamp_m5"].iloc[j],
            "entry_year": df["year"].iloc[entry_index],
            "entry_month": df["month"].iloc[entry_index],
            "entry_hour": df["hour"].iloc[entry_index]
        })

        i = j

    return equity, trades

# ============================================================
# ANALISI TRADE
# ============================================================
def analyze_trades(trades):
    if not trades:
        return {}

    pnls = np.array([t["pnl"] for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]

    total_pnl = pnls.sum()
    winrate = len(wins) / len(trades)
    avg_win = wins.mean() if len(wins) > 0 else 0.0
    avg_loss = losses.mean() if len(losses) > 0 else 0.0
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else np.inf

    equity_curve = pnls.cumsum()
    peak = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - peak
    max_dd = drawdown.min()

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
def analyze_by_group(trades, group_key):
    df = pd.DataFrame(trades)
    groups = df.groupby(group_key)

    results = []

    for key, g in groups:
        pnls = g["pnl"].values
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else np.inf
        winrate = len(wins) / len(pnls)
        avg_pnl = pnls.mean()

        results.append({
            group_key: key,
            "num_trades": len(pnls),
            "winrate": winrate,
            "profit_factor": profit_factor,
            "avg_pnl": avg_pnl
        })

    return pd.DataFrame(results).sort_values(group_key)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    model = lgb.Booster(model_file=MODEL_PATH)

    df = pd.read_csv(CSV_TEST)
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"])
    df["year"] = df["timestamp_m5"].dt.year
    df["month"] = df["timestamp_m5"].dt.month
    df["hour"] = df["timestamp_m5"].dt.hour

    X_test = df[FEATURE_COLUMNS].values
    y_pred_prob = model.predict(X_test, num_iteration=model.best_iteration)

    signals = apply_thresholding(y_pred_prob, t_buy=T_BUY, t_sell=T_SELL)

    equity, trades = run_backtest(df, signals)
    stats = analyze_trades(trades)

    print("\n=== BACKTEST RISULTATI ===")
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
