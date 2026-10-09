"""Strategie a regole con filtro di volatilita' prevista, walk-forward annuale.

Per ogni anno di test Y un modello LightGBM prevede il range delle prossime 12 barre (train < Y-1, validation Y-1).
Il filtro tiene solo le barre con volatilita' prevista nel quantile alto/basso della distribuzione del validation.
Le regole di direzione sono semplici e senza parametri ottimizzati; il controllo "random" misura il solo effetto dei costi.
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = os.path.join(os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")), "ml", "shared")
for _p in (SHARED_DIR, str(SCRIPT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from features import get_feature_columns
from walk_forward_eval_trade import load_all_years
from volatility_forecast_eval import add_vol_target, fit_lgbm
from backtest_optimized import simulate, PIP

HORIZON = 12


def rule_signals(df, seed=0):
    close, high, low = df["close_m5"], df["high_m5"], df["low_m5"]
    atr_rel = pd.to_numeric(df["atr14_m5"]) / close
    z = (close / close.shift(HORIZON) - 1) / atr_rel
    rsi = pd.to_numeric(df["rsi14_m5"])
    don_hi, don_lo = high.rolling(48).max().shift(1), low.rolling(48).min().shift(1)
    rng = np.random.default_rng(seed)
    pick = rng.random(len(df)) < 0.01
    side = rng.choice([-1, 1], len(df))
    return {
        "random": (pick & (side == 1), pick & (side == -1)),
        "momentum_1h": ((z > 2).to_numpy(), (z < -2).to_numpy()),
        "breakout_4h": ((close > don_hi).to_numpy(), (close < don_lo).to_numpy()),
        "reversion_rsi": ((rsi < 20).to_numpy(), (rsi > 80).to_numpy()),
    }


def stats_line(trades):
    if trades.empty:
        return None
    net = trades["pnl"].to_numpy() / PIP
    gross = trades["gross"].to_numpy() / PIP
    wins, losses = net[net > 0].sum(), -net[net <= 0].sum()
    t = net.mean() / (net.std(ddof=1) / np.sqrt(len(net))) if len(net) > 2 and net.std() > 0 else np.nan
    return len(net), gross.mean(), net.mean(), wins / losses if losses > 0 else np.inf, (net > 0).mean(), t


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spread-pips", type=float, default=0.8)
    parser.add_argument("--high-q", type=float, default=0.7, help="Quantile (sul validation) sopra cui la volatilita' prevista e' 'alta'")
    parser.add_argument("--low-q", type=float, default=0.3, help="Quantile (sul validation) sotto cui la volatilita' prevista e' 'bassa'")
    args = parser.parse_args()

    base = load_all_years()
    cols = get_feature_columns("new")
    df_all = add_vol_target(base, HORIZON)
    signals = rule_signals(df_all)
    for name, (lo, sh) in signals.items():
        df_all[f"{name}_long"], df_all[f"{name}_short"] = lo, sh
    years = sorted(df_all["year"].unique())
    spread = args.spread_pips * PIP
    configs = {"SL1/TP2/24b": (1.0, 2.0, 24), "SL2/TP4/48b": (2.0, 4.0, 48)}

    collected = {}
    for test_year in years[2:]:
        tr = df_all[df_all["year"] < test_year - 1].iloc[:-HORIZON]
        va = df_all[df_all["year"] == test_year - 1].iloc[:-HORIZON].reset_index(drop=True)
        te = df_all[df_all["year"] == test_year].reset_index(drop=True)
        trn, vln = tr[tr["y"].notna()], va[va["y"].notna()]
        model = fit_lgbm(trn[cols].values, trn["y"].values, vln[cols].values, vln["y"].values)
        pv = model.predict(va[cols].values, num_iteration=model.best_iteration)
        pt = model.predict(te[cols].values, num_iteration=model.best_iteration)
        hi_thr, lo_thr = np.quantile(pv, args.high_q), np.quantile(pv, args.low_q)
        masks = {"tutte le barre": None, "vol prevista ALTA": pt >= hi_thr, "vol prevista BASSA": pt <= lo_thr}
        print(f"Fold {test_year}: modello volatilita' addestrato, soglie alta/bassa (log-range) = {hi_thr:.3f}/{lo_thr:.3f}")

        for cfg_name, (sl, tp, mb) in configs.items():
            for rule in signals:
                p_long = te[f"{rule}_long"].to_numpy().astype(float)
                p_short = te[f"{rule}_short"].to_numpy().astype(float)
                for mask_name, mask in masks.items():
                    trades = simulate(te, p_long, p_short, 0.5, 0.5, spread=spread, sl_mult=sl, tp_mult=tp,
                                      max_bars=mb, signal_mask=mask)
                    collected.setdefault((cfg_name, rule, mask_name), []).append(trades)

    print(f"\nRisultati aggregati sui fold {years[2:]} | spread {args.spread_pips} pip | pips per trade, t-stat sul PNL netto\n")
    for cfg_name in configs:
        print(f"=== {cfg_name} ===")
        print(f"{'regola':<15}{'filtro':<20}{'trade':>7}{'lordo pip':>11}{'netto pip':>11}{'PF':>7}{'winrate':>9}{'t-stat':>8}")
        for rule in signals:
            for mask_name in ("tutte le barre", "vol prevista ALTA", "vol prevista BASSA"):
                parts = collected[(cfg_name, rule, mask_name)]
                trades = pd.concat([p for p in parts if not p.empty], ignore_index=True) if any(not p.empty for p in parts) else pd.DataFrame()
                s = stats_line(trades)
                if s is None:
                    print(f"{rule:<15}{mask_name:<20}{'0':>7}")
                    continue
                n, g, net, pf, wr, t = s
                print(f"{rule:<15}{mask_name:<20}{n:>7}{g:>11.2f}{net:>11.2f}{pf:>7.2f}{wr:>9.3f}{t:>8.2f}")
        print()
