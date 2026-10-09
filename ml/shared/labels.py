import numpy as np
import pandas as pd


def triple_barrier_labels(df: pd.DataFrame, tf: str = "m5", sl_mult: float = 1.0, tp_mult: float = 2.0, max_bars: int = 24, atr_col: str | None = None) -> pd.DataFrame:
    """Simula un trade long e uno short per ogni barra con SL/TP basati su ATR
    e un limite massimo di barre, usando high/low per capire quale barriera
    viene toccata per prima. Stessa logica di ensemble_atr_signal in backtest.py,
    cosi' la label riflette il trade davvero eseguibile (path-dependent),
    non solo il prezzo al termine dell'orizzonte."""
    df = df.copy()

    close = df[f"close_{tf}"].to_numpy(dtype=float)
    high = df[f"high_{tf}"].to_numpy(dtype=float)
    low = df[f"low_{tf}"].to_numpy(dtype=float)
    atr = pd.to_numeric(df[atr_col or f"atr14_{tf}"], errors="coerce").to_numpy(dtype=float)

    n = len(df)
    target_long = np.zeros(n, dtype=np.int8)
    target_short = np.zeros(n, dtype=np.int8)

    for i in range(n):
        atr_val = atr[i]
        if not atr_val or atr_val <= 0 or i + 1 >= n:
            continue

        entry = close[i]
        sl = sl_mult * atr_val
        tp = tp_mult * atr_val

        j = i + 1
        max_j = min(i + max_bars + 1, n)
        high_slice = high[j:max_j]
        low_slice = low[j:max_j]

        # LONG: chi viene toccato prima, TP o SL?
        tp_hits = np.where(high_slice >= entry + tp)[0]
        sl_hits = np.where(low_slice <= entry - sl)[0]
        tp_idx = tp_hits[0] if len(tp_hits) else np.inf
        sl_idx = sl_hits[0] if len(sl_hits) else np.inf
        if tp_idx < sl_idx:
            target_long[i] = 1

        # SHORT: chi viene toccato prima, TP o SL?
        tp_hits_s = np.where(low_slice <= entry - tp)[0]
        sl_hits_s = np.where(high_slice >= entry + sl)[0]
        tp_idx_s = tp_hits_s[0] if len(tp_hits_s) else np.inf
        sl_idx_s = sl_hits_s[0] if len(sl_hits_s) else np.inf
        if tp_idx_s < sl_idx_s:
            target_short[i] = 1

    df[f"target_long_tb_{tf}"] = target_long
    df[f"target_short_tb_{tf}"] = target_short
    return df
