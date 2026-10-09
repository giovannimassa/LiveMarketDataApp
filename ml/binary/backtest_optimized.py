import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SHARED_DIR = os.path.join(REPO_ROOT, "ml", "shared")

if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from features import get_feature_columns, model_suffix, add_derived_features, add_true_atr

N_MAX_BARS = 24
ATR_SL_MULT = 1.0
ATR_TP_MULT = 2.0
PIP = 0.0001

# Filtro ore/giorni storico di backtest.py (attivabile con --session-filter)
BAD_HOURS = {0, 3, 5, 12, 17, 18, 19, 20, 21, 22, 23}
BAD_WEEKDAYS = {2, 6}

# Frazioni di barre con segnale testate nella scelta della soglia
SWEEP_QUANTILES = [0.80, 0.85, 0.90, 0.95, 0.975, 0.99, 0.995, 0.999]


def compute_direction(p_long, p_short, t_long, t_short):
    long_sig = p_long > t_long
    short_sig = p_short > t_short
    conflict = np.where(p_long > p_short, 1, -1)
    return np.where(long_sig & ~short_sig, 1,
           np.where(short_sig & ~long_sig, -1,
           np.where(long_sig & short_sig, conflict, 0)))


def simulate(df, p_long, p_short, t_long, t_short, spread=0.0, entry="next-open",
             session_filter=False, sl_mult=ATR_SL_MULT, tp_mult=ATR_TP_MULT, max_bars=N_MAX_BARS,
             atr_col="atr14_m5", signal_mask=None):
    """Un solo trade alla volta. Con entry='next-open' l'ingresso e' all'open della barra
    successiva al segnale; con 'close' al close della barra del segnale (ottimistico).
    TP/SL: vince la barriera toccata per prima, a parita' di barra vince SL.
    `spread` e' il costo round-trip in unita' di prezzo.
    `signal_mask` (bool per barra) limita le barre da cui puo' partire un segnale."""
    ts = pd.to_datetime(df["timestamp_m5"], utc=True)
    opens = df["open_m5"].to_numpy(dtype=float)
    highs = df["high_m5"].to_numpy(dtype=float)
    lows = df["low_m5"].to_numpy(dtype=float)
    closes = df["close_m5"].to_numpy(dtype=float)
    atr = pd.to_numeric(df[atr_col], errors="coerce").to_numpy(dtype=float)
    n = len(df)

    direction = compute_direction(p_long, p_short, t_long, t_short)
    if signal_mask is not None:
        direction = np.where(signal_mask, direction, 0)
    if session_filter:
        bad = ts.dt.hour.isin(BAD_HOURS).to_numpy() | ts.dt.weekday.isin(BAD_WEEKDAYS).to_numpy()
        direction = np.where(bad, 0, direction)

    cands = np.flatnonzero(direction != 0)
    rows = []
    pos = 0
    while pos < len(cands):
        i = int(cands[pos])
        start = i + 1
        atr_val = atr[i]
        if start >= n:
            break
        if not np.isfinite(atr_val) or atr_val <= 0:
            pos += 1
            continue

        d = int(direction[i])
        entry_price = opens[start] if entry == "next-open" else closes[i]
        sl = sl_mult * atr_val
        tp = tp_mult * atr_val

        end = min(start + max_bars, n)
        h = highs[start:end]
        l = lows[start:end]
        if d == 1:
            tp_hits = np.flatnonzero(h >= entry_price + tp)
            sl_hits = np.flatnonzero(l <= entry_price - sl)
        else:
            tp_hits = np.flatnonzero(l <= entry_price - tp)
            sl_hits = np.flatnonzero(h >= entry_price + sl)

        size = len(h)
        tp_k = tp_hits[0] if tp_hits.size else size
        sl_k = sl_hits[0] if sl_hits.size else size

        if tp_k < sl_k:
            exit_k, exit_price, reason = tp_k, entry_price + d * tp, "TP"
        elif sl_k < size:
            exit_k, exit_price, reason = sl_k, entry_price - d * sl, "SL"
        else:
            exit_k, exit_price, reason = size - 1, closes[start + size - 1], "TIME"

        exit_idx = start + exit_k
        gross = d * (exit_price - entry_price)
        rows.append({
            "entry_index": i, "exit_index": exit_idx, "direction": d,
            "entry_price": entry_price, "exit_price": exit_price,
            "gross": gross, "pnl": gross - spread, "reason": reason,
            "entry_time": ts.iloc[i], "entry_year": ts.iloc[i].year,
            "pLong": p_long[i], "pShort": p_short[i],
        })
        pos = int(np.searchsorted(cands, exit_idx, side="right"))

    return pd.DataFrame(rows)


def summarize(trades):
    if trades.empty:
        return {"num_trades": 0, "gross_pnl": 0.0, "net_pnl": 0.0, "winrate": 0.0,
                "profit_factor": 0.0, "max_drawdown": 0.0, "avg_net_pips": 0.0}
    pnl = trades["pnl"].to_numpy()
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    curve = pnl.cumsum()
    return {
        "num_trades": len(pnl),
        "gross_pnl": float(trades["gross"].sum()),
        "net_pnl": float(pnl.sum()),
        "winrate": len(wins) / len(pnl),
        "profit_factor": wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf,
        "max_drawdown": float((curve - np.maximum.accumulate(curve)).min()),
        "avg_net_pips": float(pnl.mean() / PIP),
    }


def select_thresholds(df, p_long, p_short, spread, min_trades=100, **sim_kwargs):
    """Sceglie la frazione di barre con segnale che massimizza il PnL netto sul set passato.
    Le soglie sono i quantili delle probabilita' di ciascun modello su questo stesso set."""
    best, table = None, []
    mask = sim_kwargs.get("signal_mask")
    q_long, q_short = (p_long, p_short) if mask is None else (p_long[mask], p_short[mask])
    for q in SWEEP_QUANTILES:
        t_long, t_short = float(np.quantile(q_long, q)), float(np.quantile(q_short, q))
        stats = summarize(simulate(df, p_long, p_short, t_long, t_short, spread=spread, **sim_kwargs))
        table.append({"quantile": q, "t_long": t_long, "t_short": t_short, **stats})
        if stats["num_trades"] >= min_trades and (best is None or stats["net_pnl"] > best["net_pnl"]):
            best = table[-1]
    if best is None:
        best = max(table, key=lambda r: r["num_trades"])
    return best, pd.DataFrame(table)


def load_df(path, true_atr=False):
    df = add_derived_features(pd.read_csv(path))
    df["timestamp_m5"] = pd.to_datetime(df["timestamp_m5"], utc=True)
    return add_true_atr(df) if true_atr else df


def print_summary(label, stats, trades):
    print(f"\n=== {label} ===")
    print(f"Trade: {stats['num_trades']}  PNL lordo: {stats['gross_pnl']:.5f}  PNL netto: {stats['net_pnl']:.5f}  "
          f"Pips netti/trade: {stats['avg_net_pips']:.3f}")
    print(f"Winrate: {stats['winrate']:.3f}  Profit factor: {stats['profit_factor']:.3f}  Max DD: {stats['max_drawdown']:.5f}")
    if not trades.empty:
        by_year = trades.groupby("entry_year")["pnl"].agg(
            num_trades="count", net_pnl="sum",
            profit_factor=lambda s: s[s > 0].sum() / abs(s[s <= 0].sum()) if (s <= 0).any() and s[s <= 0].sum() != 0 else np.inf)
        print(by_year)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-set", choices=["new", "legacy"], default=os.environ.get("FEATURE_SET", "new"))
    parser.add_argument("--model-suffix", default=None, help="Suffisso dei file modello (default: legato al feature-set)")
    parser.add_argument("--spread-pips", type=float, default=0.8, help="Costo round-trip in pip (default 0.8)")
    parser.add_argument("--entry", choices=["next-open", "close"], default="next-open")
    parser.add_argument("--t-long", type=float, default=0.20)
    parser.add_argument("--t-short", type=float, default=0.20)
    parser.add_argument("--select-threshold", action="store_true",
                        help="Sceglie la soglia sul validation set (PnL netto) e la applica al test")
    parser.add_argument("--min-trades", type=int, default=100, help="Trade minimi per accettare una soglia")
    parser.add_argument("--session-filter", action="store_true", help="Esclude le ore/giorni di BAD_HOURS/BAD_WEEKDAYS")
    parser.add_argument("--true-atr", action="store_true", help="Usa per SL/TP l'ATR ricalcolato dagli OHLC (atr14 del dataset e' gonfiato)")
    args = parser.parse_args()

    start = time.time()
    suffix = args.model_suffix if args.model_suffix is not None else model_suffix(args.feature_set)
    cols = get_feature_columns(args.feature_set)
    model_long = lgb.Booster(model_file=str(SCRIPT_DIR / f"model_long_atr{suffix}.txt"))
    model_short = lgb.Booster(model_file=str(SCRIPT_DIR / f"model_short_atr{suffix}.txt"))
    spread = args.spread_pips * PIP
    kw = {"entry": args.entry, "session_filter": args.session_filter}
    if args.true_atr:
        kw["atr_col"] = "atr_true_m5"

    t_long, t_short = args.t_long, args.t_short
    if args.select_threshold:
        valid = load_df(ML_DIR / "eurusd_valid.csv", args.true_atr)
        pv_long = model_long.predict(valid[cols].values)
        pv_short = model_short.predict(valid[cols].values)
        best, table = select_thresholds(valid, pv_long, pv_short, spread, min_trades=args.min_trades, **kw)
        print("=== SCELTA SOGLIA SU VALIDATION ===")
        print(table.to_string(index=False))
        t_long, t_short = best["t_long"], best["t_short"]
        print(f"Scelta: quantile={best['quantile']} t_long={t_long:.4f} t_short={t_short:.4f}")

    test = load_df(ML_DIR / "eurusd_test.csv", args.true_atr)
    p_long = model_long.predict(test[cols].values)
    p_short = model_short.predict(test[cols].values)
    trades = simulate(test, p_long, p_short, t_long, t_short, spread=spread, **kw)
    print_summary(f"TEST (spread {args.spread_pips} pip, entry {args.entry}, t_long={t_long:.4f}, t_short={t_short:.4f})",
                  summarize(trades), trades)
    print(f"\nTempo totale: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
