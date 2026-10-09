import argparse
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

from features import get_feature_columns, model_suffix, add_derived_features

_parser = argparse.ArgumentParser()
_parser.add_argument(
    "--feature-set",
    choices=["new", "legacy"],
    default=os.environ.get("FEATURE_SET", "new"),
    help="Elenco di feature usato dai modelli da testare (default: new)",
)
_parser.add_argument(
    "--model-suffix",
    default=None,
    help="Suffisso dei file modello da caricare (default: quello legato al feature-set, es. _legacy)",
)
_args, _ = _parser.parse_known_args()

FEATURE_COLUMNS = get_feature_columns(_args.feature_set)
_suffix = _args.model_suffix if _args.model_suffix is not None else model_suffix(_args.feature_set)

# ============================================================
# CONFIG
# ============================================================
CSV_TEST = ML_DIR / "eurusd_test.csv"

MODEL_LONG_ATR_PATH = SCRIPT_DIR / f"model_long_atr{_suffix}.txt"
MODEL_SHORT_ATR_PATH = SCRIPT_DIR / f"model_short_atr{_suffix}.txt"

T_LONG_ATR = 0.20
T_SHORT_ATR = 0.20

N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0

# ============================================================
# MODELLI
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

    if long_signal and not short_signal:
        return 1, pLongAtr, pShortAtr
    if short_signal and not long_signal:
        return -1, pLongAtr, pShortAtr
    if long_signal and short_signal:
        return (1 if pLongAtr > pShortAtr else -1), pLongAtr, pShortAtr

    return 0, pLongAtr, pShortAtr

# ============================================================
# BACKTEST ENGINE (OTTIMIZZATO)
# ============================================================
def run_backtest(df):
    equity = 0.0
    trades = []

    X = df[FEATURE_COLUMNS].values
    prices = df["close_m5"].values
    atr = df["atr14_m5"].values
    highs = df["high_m5"].values
    lows = df["low_m5"].values

    timestamps = df["timestamp_m5"].values
    years = df["year"].values
    months = df["month"].values
    hours = df["hour"].values
    weekdays = df["weekday"].values

    i = 0
    n = len(df)

    # Filtri da escludere:
    # - Escludiamo alcuni orari in cui non vogliamo operare
    # - Escludiamo alcuni giorni della settimana (es. weekend)
    bad_hours = {0, 3, 5, 12, 17, 18, 19, 20, 21, 22, 23}
    bad_weekdays = {2, 6}

    while i < n:

        if hours[i] in bad_hours or weekdays[i] in bad_weekdays:
            i += 1
            continue

        x = X[i:i+1]
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

        j = i + 1
        max_j = min(i + N_MAX_BARS + 1, n)

        high_slice = highs[j:max_j]
        low_slice = lows[j:max_j]

        if direction == 1:
            tp_hits = np.where(high_slice >= entry_price + tp)[0]
            sl_hits = np.where(low_slice <= entry_price - sl)[0]
            tp_idx = tp_hits[0] if len(tp_hits) > 0 else None
            sl_idx = sl_hits[0] if len(sl_hits) > 0 else None

            if tp_idx is not None and (sl_idx is None or tp_idx < sl_idx):
                exit_index = j + tp_idx
                exit_price = entry_price + tp
                exit_reason = "TP"
            elif sl_idx is not None:
                exit_index = j + sl_idx
                exit_price = entry_price - sl
                exit_reason = "SL"
            else:
                exit_index = max_j - 1
                exit_price = prices[exit_index]
                exit_reason = "TIME"
        else:
            tp_hits = np.where(low_slice <= entry_price - tp)[0]
            sl_hits = np.where(high_slice >= entry_price + sl)[0]
            tp_idx = tp_hits[0] if len(tp_hits) > 0 else None
            sl_idx = sl_hits[0] if len(sl_hits) > 0 else None

            if tp_idx is not None and (sl_idx is None or tp_idx < sl_idx):
                exit_index = j + tp_idx
                exit_price = entry_price - tp
                exit_reason = "TP"
            elif sl_idx is not None:
                exit_index = j + sl_idx
                exit_price = entry_price + sl
                exit_reason = "SL"
            else:
                exit_index = max_j - 1
                exit_price = prices[exit_index]
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
            "entry_time": timestamps[entry_index],
            "exit_time": timestamps[exit_idx],
            "entry_year": years[entry_index],
            "entry_month": months[entry_index],
            "entry_hour": hours[entry_index],
            "entry_weekday": weekdays[entry_index],
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
    winrate = len(wins) / len(trades)
    profit_factor = wins.sum() / abs(losses.sum()) if len(losses) else np.inf

    equity_curve = pnls.cumsum()
    peak = np.maximum.accumulate(equity_curve)
    drawdown = equity_curve - peak
    max_dd = drawdown.min()

    return {
        "num_trades": len(trades),
        "total_pnl": total_pnl,
        "winrate": winrate,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
        "equity_curve": equity_curve
    }

# ============================================================
# ANALISI PER GRUPPO (ANNO / MESE / ORA / WEEKDAY)
# ============================================================
def analyze_by_group(trades, key):
    df = pd.DataFrame(trades)
    groups = df.groupby(key)

    rows = []
    for k, g in groups:
        pnls = g["pnl"].values
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]

        profit_factor = wins.sum() / abs(losses.sum()) if len(losses) else np.inf
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

    df = add_derived_features(pd.read_csv(CSV_TEST))
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"])
    df["year"] = df["timestamp_m5"].dt.year
    df["month"] = df["timestamp_m5"].dt.month
    df["hour"] = df["timestamp_m5"].dt.hour
    df["weekday"] = df["timestamp_m5"].dt.weekday  # 0=Lunedì, 6=Domenica

    equity, trades = run_backtest(df)
    stats = analyze_trades(trades)

    print("\n=== RISULTATI BACKTEST ENSEMBLE ATR ===")
    print("Numero trade:", stats["num_trades"])
    print("PNL totale:", stats["total_pnl"])
    print("Winrate:", stats["winrate"])
    print("Profit factor:", stats["profit_factor"])
    print("Max drawdown:", stats["max_drawdown"])
    print("Equity curve:", stats["equity_curve"])

    print("\n=== ANALISI PER ANNO ===")
    print(analyze_by_group(trades, "entry_year"))

    print("\n=== ANALISI PER MESE ===")
    print(analyze_by_group(trades, "entry_month"))

    print("\n=== ANALISI PER ORA ===")
    print(analyze_by_group(trades, "entry_hour"))

    print("\n=== ANALISI PER GIORNO DELLA SETTIMANA ===")
    print(analyze_by_group(trades, "entry_weekday"))

    elapsed = time.time() - start_time
    print(f"\nTempo totale: {elapsed:.2f}s")