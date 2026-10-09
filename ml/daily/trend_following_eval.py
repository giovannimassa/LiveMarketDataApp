"""Test di plausibilita' economica: trend following giornaliero (time-series momentum) con costi.

Nessun parametro viene ottimizzato: i lookback 20/60/120/250 sono riportati tutti e l'insieme (media dei segnali)
e' la specifica dichiarata a priori. Volatility targeting opzionale. Il segnale a fine giornata t viene tenuto
dal close di t al close di t+1; il costo e' metà spread per unita' di turnover. Swap/carry non sono inclusi.
Test di permutazione: il segnale viene traslato circolarmente di lag casuali (preserva la persistenza).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DAILY_DIR = Path(__file__).resolve().parent
LOOKBACKS = [20, 60, 120, 250]
PERIODS = {"2003-2009": ("2003", "2009"), "2010-2019": ("2010", "2019"), "2020-oggi": ("2020", "2030")}


def load_pair(name):
    df = pd.read_csv(DAILY_DIR / f"{name}_d1.csv")
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None).dt.normalize()
    df = df[df["date"].dt.dayofweek < 5].drop_duplicates("date").set_index("date").sort_index()
    max_gap = df.index.to_series().diff().dt.days.max()
    if max_gap > 6:
        raise ValueError(f"{name}: buco di {max_gap} giorni nella serie, scaricare di nuovo gli anni mancanti")
    return df[df["high"] > df["low"]]


def signal_from_lookbacks(close, lookbacks):
    sigs = [np.sign(close / close.shift(lb) - 1) for lb in lookbacks]
    return pd.concat(sigs, axis=1).mean(axis=1)


def run(close, signal, spread_pips, pip, target_vol, cap):
    ret = close.pct_change()
    if target_vol:
        vol = ret.ewm(halflife=20).std() * np.sqrt(252)
        lev = (target_vol / vol).clip(upper=cap)
    else:
        lev = pd.Series(1.0, index=close.index)
    pos = (signal * lev).fillna(0.0)
    held = pos.shift(1)
    turnover = (pos - pos.shift(1)).abs().shift(1)
    cost = (spread_pips * pip / 2) / close.shift(1)
    gross = (held * ret).dropna()
    net = (gross - (cost * turnover).reindex(gross.index).fillna(0.0))
    return gross, net, pos


def perf(r):
    r = r.dropna()
    if len(r) < 50 or r.std() == 0:
        return {"sharpe": np.nan, "ann_ret": np.nan, "vol": np.nan, "maxdd": np.nan, "t": np.nan}
    equity = (1 + r).cumprod()
    return {"sharpe": r.mean() / r.std() * np.sqrt(252), "ann_ret": r.mean() * 252, "vol": r.std() * np.sqrt(252),
            "maxdd": (equity / equity.cummax() - 1).min(), "t": r.mean() / (r.std() / np.sqrt(len(r)))}


def row(label, gross, net, pos):
    pg, pn = perf(gross), perf(net)
    turn = (pos - pos.shift(1)).abs().mean() * 252
    per = " ".join(f"{perf(net.loc[a:b])['sharpe']:>6.2f}" for a, b in PERIODS.values())
    print(f"{label:<24}{pg['sharpe']:>8.2f}{pn['sharpe']:>8.2f}{pn['ann_ret'] * 100:>8.1f}%{pn['vol'] * 100:>7.1f}%"
          f"{pn['maxdd'] * 100:>8.1f}%{turn:>8.1f}{pn['t']:>7.2f}  | {per}")


def permutation_pvalue(close, signal, spread_pips, pip, target_vol, cap, observed, n=500, seed=0):
    rng = np.random.default_rng(seed)
    sig = signal.to_numpy()
    null = []
    for _ in range(n):
        k = int(rng.integers(260, len(sig) - 260))
        shifted = pd.Series(np.roll(sig, k), index=signal.index)
        _, net, _ = run(close, shifted, spread_pips, pip, target_vol, cap)
        null.append(perf(net)["sharpe"])
    null = np.array(null)
    return float(np.mean(null >= observed)), float(np.nanmean(null)), float(np.nanstd(null))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", nargs="+", default=["eurusd"])
    parser.add_argument("--spread-pips", type=float, default=1.0)
    parser.add_argument("--target-vol", type=float, default=0.10)
    parser.add_argument("--cap", type=float, default=4.0)
    args = parser.parse_args()

    port_net, port_gross = [], []
    for name in args.pairs:
        df = load_pair(name)
        close = df["close"]
        pip = 0.01 if "jpy" in name else 0.0001
        print(f"\n===== {name.upper()} giornaliero: {close.index[0].date()} -> {close.index[-1].date()} ({len(close)} giorni), "
              f"spread {args.spread_pips} pip, target vol {args.target_vol:.0%}, leva max {args.cap} =====")
        print(f"{'strategia':<24}{'SR lordo':>8}{'SR netto':>8}{'rend/anno':>9}{'vol':>8}{'maxDD':>9}{'turnover':>8}{'t':>7}  | Sharpe netto {' '.join(PERIODS)}")

        bh = close.pct_change().dropna()
        row("buy & hold", bh, bh, pd.Series(1.0, index=close.index))
        for lb in LOOKBACKS:
            sig = signal_from_lookbacks(close, [lb])
            g, n, p = run(close, sig, args.spread_pips, pip, args.target_vol, args.cap)
            row(f"trend L={lb} (vol target)", g, n, p)
        ens = signal_from_lookbacks(close, LOOKBACKS)
        g, n, p = run(close, ens, args.spread_pips, pip, args.target_vol, args.cap)
        row("INSIEME (vol target)", g, n, p)
        g1, n1, p1 = run(close, ens, args.spread_pips, pip, None, args.cap)
        row("INSIEME (taglia fissa)", g1, n1, p1)
        port_net.append(n.rename(name))
        port_gross.append(g.rename(name))

        obs = perf(n)["sharpe"]
        pval, nm, ns = permutation_pvalue(close, ens, args.spread_pips, pip, args.target_vol, args.cap, obs)
        print(f"Permutazione (500 traslazioni circolari del segnale): Sharpe netto osservato {obs:.2f} vs nullo {nm:.2f} +/- {ns:.2f}, p = {pval:.3f}")

    if len(args.pairs) > 1:
        pn = pd.concat(port_net, axis=1).dropna(how="all").fillna(0).mean(axis=1)
        pg = pd.concat(port_gross, axis=1).dropna(how="all").fillna(0).mean(axis=1)
        print(f"\n===== PORTAFOGLIO equal-weight di {len(args.pairs)} coppie (INSIEME, vol target) =====")
        print(f"{'':<24}{'SR lordo':>8}{'SR netto':>8}{'rend/anno':>9}{'vol':>8}{'maxDD':>9}{'turnover':>8}{'t':>7}  | Sharpe netto {' '.join(PERIODS)}")
        row("portafoglio", pg, pn, pd.Series(0.0, index=pn.index))
