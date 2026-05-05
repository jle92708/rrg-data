"""
Alpaca live data generator for the Rotation Terminal artifact.
Runs daily via GitHub Actions. Outputs market_data.json.
"""
import json
import os
import sys
import time
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
except ImportError:
    print("ERROR: alpaca-py not installed.")
    sys.exit(1)

warnings.filterwarnings("ignore")

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")

if not API_KEY or not API_SECRET:
    print("ERROR: Alpaca credentials missing in environment.")
    sys.exit(1)

BENCHMARK = "SPY"

SECTORS = {
    "XLK":  {"name": "Technology",          "color": "#22d3ee"},
    "XLY":  {"name": "Cons. Discretionary", "color": "#a78bfa"},
    "XLI":  {"name": "Industrials",         "color": "#34d399"},
    "XLC":  {"name": "Communication Svc.",  "color": "#fbbf24"},
    "XLP":  {"name": "Cons. Staples",       "color": "#a3e635"},
    "XLU":  {"name": "Utilities",           "color": "#fb7185"},
    "XLRE": {"name": "Real Estate",         "color": "#f472b6"},
    "XLE":  {"name": "Energy",              "color": "#c084fc"},
    "XLV":  {"name": "Health Care",         "color": "#2dd4bf"},
    "XLF":  {"name": "Financials",          "color": "#60a5fa"},
    "XLB":  {"name": "Materials",           "color": "#fb923c"},
}

INDUSTRIES = {
    "XLK": {
        "SOFT":  {"name": "Software",       "color": "#06b6d4", "stocks": ["MSFT","ORCL","ADBE","CRM","NOW"]},
        "SEMI":  {"name": "Semiconductors", "color": "#0891b2", "stocks": ["NVDA","AVGO","AMD","QCOM","TXN","MU"]},
        "HARD":  {"name": "Hardware & IT",  "color": "#155e75", "stocks": ["AAPL","CSCO","DELL","IBM"]},
    },
    "XLF": {
        "BANK":   {"name": "Banks",           "color": "#3b82f6", "stocks": ["JPM","BAC","WFC","C","USB"]},
        "INS":    {"name": "Insurance",       "color": "#2563eb", "stocks": ["PGR","CB","AIG","TRV"]},
        "CAPMKT": {"name": "Capital Markets", "color": "#1d4ed8", "stocks": ["GS","MS","BLK","SCHW"]},
        "CARDS":  {"name": "Payments",        "color": "#1e40af", "stocks": ["V","MA","AXP"]},
    },
    "XLI": {
        "MACH":  {"name": "Machinery",  "color": "#10b981", "stocks": ["CAT","DE","ETN","EMR"]},
        "DEF":   {"name": "Defense",    "color": "#059669", "stocks": ["RTX","LMT","NOC","GD","BA"]},
        "TRANS": {"name": "Transports", "color": "#047857", "stocks": ["UNP","UPS","FDX","CSX","DAL"]},
    },
    "XLY": {
        "RETAIL": {"name": "Retail",       "color": "#c4b5fd", "stocks": ["AMZN","EBAY"]},
        "AUTO":   {"name": "Auto",         "color": "#e9d5ff", "stocks": ["TSLA","F","GM"]},
        "HOME":   {"name": "Homebuilders", "color": "#d8b4fe", "stocks": ["DHI","LEN","NVR","PHM"]},
        "REST":   {"name": "Restaurants",  "color": "#f3e8ff", "stocks": ["MCD","SBUX","CMG","BKNG"]},
    },
    "XLE": {
        "OIL":  {"name": "Oil & Gas",     "color": "#a855f7", "stocks": ["XOM","CVX","COP","EOG"]},
        "PIPE": {"name": "Pipelines",     "color": "#7e22ce", "stocks": ["KMI","WMB","OKE"]},
    },
    "XLV": {
        "PHRMA":   {"name": "Pharma",   "color": "#14b8a6", "stocks": ["LLY","JNJ","PFE","MRK","ABBV"]},
        "BIOTECH": {"name": "Biotech",  "color": "#0d9488", "stocks": ["AMGN","GILD","VRTX","REGN"]},
        "MEDDEV":  {"name": "Devices",  "color": "#0f766e", "stocks": ["ISRG","ABT","MDT","SYK"]},
        "HCSVC":   {"name": "Services", "color": "#115e59", "stocks": ["UNH","CVS","CI","ELV"]},
    },
    "XLC": {
        "INET":  {"name": "Internet", "color": "#fcd34d", "stocks": ["GOOGL","META"]},
        "TELCO": {"name": "Telecom",  "color": "#fde047", "stocks": ["VZ","T","TMUS"]},
        "MEDIA": {"name": "Media",    "color": "#facc15", "stocks": ["DIS","NFLX","CMCSA"]},
    },
    "XLP": {
        "BEV":     {"name": "Beverages", "color": "#84cc16", "stocks": ["KO","PEP","MO","PM"]},
        "GROCERY": {"name": "Grocery",   "color": "#65a30d", "stocks": ["WMT","COST","KR"]},
        "HOUSE":   {"name": "Household", "color": "#4d7c0f", "stocks": ["PG","CL","KMB"]},
    },
    "XLB": {
        "CHEM":  {"name": "Chemicals",   "color": "#f97316", "stocks": ["LIN","SHW","APD","ECL"]},
        "METAL": {"name": "Metals",      "color": "#ea580c", "stocks": ["FCX","NEM","NUE"]},
    },
    "XLU": {
        "ELEC":  {"name": "Electric Util", "color": "#fb7185", "stocks": ["NEE","DUK","SO","AEP"]},
        "WATER": {"name": "Water Util",    "color": "#f43f5e", "stocks": ["AWK","XEL"]},
    },
    "XLRE": {
        "RESI": {"name": "Residential REITs", "color": "#f472b6", "stocks": ["AVB","EQR","INVH"]},
        "COMM": {"name": "Commercial REITs",  "color": "#ec4899", "stocks": ["PLD","SPG","O"]},
        "SPEC": {"name": "Specialty REITs",   "color": "#db2777", "stocks": ["AMT","EQIX","CCI","PSA"]},
    },
}

client = StockHistoricalDataClient(API_KEY, API_SECRET)

def fetch_prices(tickers, lookback_days=400):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    print(f"Fetching {len(tickers)} tickers from Alpaca...")
    all_bars = []
    for i in range(0, len(tickers), 100):
        chunk = tickers[i:i + 100]
        try:
            req = StockBarsRequest(symbol_or_symbols=chunk, timeframe=TimeFrame.Day,
                                   start=start, end=end, adjustment="all", feed="iex")
            bars = client.get_stock_bars(req)
            if bars.df is not None and not bars.df.empty:
                all_bars.append(bars.df)
        except Exception as e:
            print(f"Chunk failed: {e}")
        time.sleep(0.3)
    if not all_bars:
        raise RuntimeError("No bars returned.")
    full = pd.concat(all_bars)
    close = full["close"].unstack(level=0)
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    return close[~close.index.duplicated(keep="last")].sort_index().ffill()

def compute_rs(price_df, bench_col, period="weekly", lookback=63):
    bench = price_df[bench_col]
    if period == "weekly":
        price_df = price_df.resample("W-FRI").last()
        bench = bench.resample("W-FRI").last()
    out = {}
    for ticker in price_df.columns:
        if ticker == bench_col: continue
        s = price_df[ticker].dropna()
        if len(s) < 50: continue
        rs_raw = s / bench.reindex(s.index)
        rs_smooth = rs_raw.ewm(span=10, adjust=False).mean()
        rm = rs_smooth.rolling(window=lookback, min_periods=20).mean()
        rstd = rs_smooth.rolling(window=lookback, min_periods=20).std()
        z = (rs_smooth - rm) / rstd.replace(0, np.nan)
        rr = (100 + z * 2.5).clip(lower=92, upper=108)
        rmom = (100 + (rr - rr.shift(5)) * 1.5).clip(lower=92, upper=108)
        out[ticker] = {"rr": rr, "rm": rmom}
    return out

def get_trail(rs, ticker, tail=8):
    if ticker not in rs: return [], None
    rr = rs[ticker]["rr"].dropna()
    rm = rs[ticker]["rm"].dropna()
    common = rr.index.intersection(rm.index)
    if len(common) < 2: return [], None
    rr = rr.loc[common].tail(tail); rm = rm.loc[common].tail(tail)
    trail = [{"r": round(float(a), 3), "m": round(float(b), 3)} for a, b in zip(rr.values, rm.values)]
    return trail, (trail[-1] if trail else None)

def quadrant(r, m):
    if r >= 100 and m >= 100: return "leading"
    if r >= 100 and m < 100:  return "weakening"
    if r < 100 and m < 100:   return "lagging"
    return "improving"

def compute_sctr(prices):
    today = prices.iloc[-1]
    roc125 = (today / prices.iloc[-125] - 1) * 100 if len(prices) >= 125 else pd.Series(0, index=today.index)
    pct200 = (today / prices.rolling(200).mean().iloc[-1] - 1) * 100
    roc20 = (today / prices.iloc[-20] - 1) * 100 if len(prices) >= 20 else pd.Series(0, index=today.index)
    pct50 = (today / prices.rolling(50).mean().iloc[-1] - 1) * 100
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = (100 - 100 / (1 + gain / loss.replace(0, np.nan))).iloc[-1]
    e12 = prices.ewm(span=12, adjust=False).mean()
    e26 = prices.ewm(span=26, adjust=False).mean()
    ppo = (e12 - e26) / e26 * 100
    ppoh = ppo - ppo.ewm(span=9, adjust=False).mean()
    pslope = ppoh.iloc[-1] - ppoh.iloc[-4] if len(ppoh) >= 4 else pd.Series(0, index=today.index)
    comp = pd.DataFrame({"a": roc125, "b": pct200, "c": roc20, "d": pct50, "e": rsi, "f": pslope})
    pct = comp.rank(pct=True) * 100
    return (0.30 * pct["a"] + 0.30 * pct["b"] + 0.15 * pct["c"] + 0.15 * pct["d"]
            + 0.05 * pct["e"] + 0.05 * pct["f"]).round(0).fillna(0).astype(int)

def ret(prices, t, days):
    if t not in prices.columns: return 0.0
    s = prices[t].dropna()
    if len(s) < days + 1: return 0.0
    return round((s.iloc[-1] / s.iloc[-days - 1] - 1) * 100, 2)

def build():
    tickers = {BENCHMARK} | set(SECTORS.keys())
    for sec, inds in INDUSTRIES.items():
        for ind, info in inds.items():
            tickers.update(info["stocks"])
    prices = fetch_prices(sorted(tickers))
    if BENCHMARK not in prices.columns:
        raise RuntimeError(f"{BENCHMARK} missing")
    rs = compute_rs(prices, BENCHMARK, "weekly")
    sctr = compute_sctr(prices.drop(columns=[BENCHMARK], errors="ignore"))
    sectors = []
    for tk, meta in SECTORS.items():
        trail, cur = get_trail(rs, tk, 8)
        if cur is None: continue
        sectors.append({"ticker": tk, "name": meta["name"], "color": meta["color"],
                        "trail": trail, "current": cur,
                        "quadrant": quadrant(cur["r"], cur["m"]),
                        "rs": {"ratio": cur["r"], "momentum": cur["m"]}})
    drilldown = {}
    for sec_tk, ind_dict in INDUSTRIES.items():
        sec_inds = {}
        for ind_k, ind_info in ind_dict.items():
            stks = [t for t in ind_info["stocks"] if t in prices.columns]
            if not stks: continue
            idx = prices[stks].mean(axis=1).rename("__i__")
            ind_frame = pd.concat([idx, prices[BENCHMARK]], axis=1)
            ind_rs = compute_rs(ind_frame, BENCHMARK, "weekly")
            _, ind_cur = get_trail(ind_rs, "__i__", 2)
            irr = ind_cur["r"] if ind_cur else 100.0
            irm = ind_cur["m"] if ind_cur else 100.0
            isctr = int(np.mean([int(sctr.get(t, 0)) for t in stks]))
            stocks_pl = []
            for st in stks:
                ssctr = int(sctr.get(st, 0))
                pr = int(round((sctr < ssctr).sum() / max(1, len(sctr)) * 100)) if not sctr.empty else 0
                stocks_pl.append({"ticker": st, "name": st,
                                  "price": round(float(prices[st].dropna().iloc[-1]), 2),
                                  "sctr": ssctr, "pctRank": pr,
                                  "r1": ret(prices, st, 21),
                                  "r3": ret(prices, st, 63),
                                  "r6": ret(prices, st, 126)})
            stocks_pl.sort(key=lambda x: x["sctr"], reverse=True)
            sec_inds[ind_k] = {"name": ind_info["name"], "color": ind_info["color"],
                               "rs": {"ratio": round(irr, 2), "momentum": round(irm, 2)},
                               "sctr": isctr, "stocks": stocks_pl}
        drilldown[sec_tk] = {"industries": sec_inds}
    return {"generatedAt": datetime.utcnow().isoformat() + "Z",
            "source": "alpaca", "benchmark": BENCHMARK,
            "tail": 8, "period": "weekly",
            "sectors": sectors, "drilldown": drilldown}

if __name__ == "__main__":
    Path("docs").mkdir(exist_ok=True)
    payload = build()
    Path("docs/market_data.json").write_text(json.dumps(payload, indent=2))
    print(f"Wrote market_data.json — {len(payload['sectors'])} sectors")
