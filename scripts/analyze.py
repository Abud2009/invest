# -*- coding: utf-8 -*-
"""Overnight-session analysis for a Czech investor (Europe/Prague).
Buy at 00:00 CET, hold through the night, sell at 08:00 CET."""
import pandas as pd, numpy as np, json
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")
CAPITAL = 2000  # Kč

def load(name):
    df = pd.read_csv(f"data_{name}.csv")
    df["dt"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert(PRAGUE)
    df = df.set_index("dt").sort_index()
    return df

def overnight_stats(df, label):
    """All nights where we have full 00:00 -> 08:00 coverage."""
    nights = []
    for day, g in df.groupby(df.index.date):
        g = g.between_time("00:00", "08:00")
        if len(g) < 7:  # need hourly bars 00..07 plus entry at 00:00
            continue
        entry = g["open"].iloc[0] if not np.isnan(g["open"].iloc[0]) else g["close"].iloc[0]
        path = [entry] + list(g["close"].iloc[:8])
        if len(path) < 9:
            continue
        ret8 = path[-1] / entry - 1
        path = np.array(path)
        nights.append({
            "date": str(day),
            "dow": pd.Timestamp(day).day_name(),
            "ret8": ret8,
            "maxup": (path.max() / entry - 1),
            "maxdn": (path.min() / entry - 1),
            "hours": list(path / entry - 1),
        })
    n = pd.DataFrame([{k: v for k, v in d.items() if k != "hours"} for d in nights])
    return n, nights

out = {}

for name in ["BTC", "ETH", "GOLD", "EURUSD"]:
    df = load(name)
    n, nights = overnight_stats(df, name)
    is_weekend = n["dow"].isin(["Saturday", "Sunday"])  # night Sat/Sun morning
    # For Friday night (00:00 Saturday) weekend; note dow of the 00:00 day
    stats = {}
    for grp, mask in [("all", np.ones(len(n), bool)),
                      ("weekday_nights", ~is_weekend),
                      ("weekend_nights", is_weekend)]:
        s = n[mask]
        r = s["ret8"]
        stats[grp] = {
            "n": int(len(s)),
            "mean_pct": round(100 * r.mean(), 3),
            "median_pct": round(100 * r.median(), 3),
            "sd_pct": round(100 * r.std(), 3),
            "min_pct": round(100 * r.min(), 2),
            "max_pct": round(100 * r.max(), 2),
            "p5_pct": round(100 * r.quantile(0.05), 2),
            "p95_pct": round(100 * r.quantile(0.95), 2),
            "p_pos": round(100 * (r > 0).mean(), 1),
            "p_gt1": round(100 * (r > 0.01).mean(), 1),
            "p_lt1": round(100 * (r < -0.01).mean(), 1),
            "p_gt2": round(100 * (r > 0.02).mean(), 1),
            "p_lt2": round(100 * (r < -0.02).mean(), 1),
            "p_gt3": round(100 * (r > 0.03).mean(), 1),
            "p_lt3": round(100 * (r < -0.03).mean(), 1),
            "mean_maxup_pct": round(100 * s["maxup"].mean(), 2),
            "mean_maxdn_pct": round(100 * s["maxdn"].mean(), 2),
            "mean_kc": round(CAPITAL * r.mean(), 1),
            "p5_kc": round(CAPITAL * r.quantile(0.05), 0),
            "p95_kc": round(CAPITAL * r.quantile(0.95), 0),
            "worst_kc": round(CAPITAL * r.min(), 0),
            "best_kc": round(CAPITAL * r.max(), 0),
        }
    # hourly trajectory (CET hours 0..8): mean return vs entry, P(profit)
    H = np.array([d["hours"] for d in nights])
    traj = {
        "hours_cet": list(range(9)),
        "mean_pct": [round(100 * x, 3) for x in H.mean(axis=0)],
        "p_pos": [round(100 * (H[:, i] > 0).mean(), 1) for i in range(9)],
        "mean_kc": [round(CAPITAL * x, 1) for x in H.mean(axis=0)],
    }
    # hourly profile: per-CET-hour returns across whole sample
    df["hour"] = df.index.hour
    df["ret"] = df["close"].pct_change()
    prof = df.groupby("hour")["ret"].agg(["mean", "std", "count"])
    prof["pct_pos"] = df.groupby("hour").apply(lambda g: 100 * (g["ret"] > 0).mean())
    hourly_profile = {
        "hour_cet": [int(h) for h in prof.index],
        "mean_bp": [round(10000 * x, 2) for x in prof["mean"]],
        "sd_pct": [round(100 * x, 3) for x in prof["std"]],
        "pct_pos": [round(x, 1) for x in prof["pct_pos"]],
    }
    out[name] = {"overnight": stats, "trajectory": traj, "hourly_profile": hourly_profile}

# stop-loss simulation on BTC weekend nights: stop at -2%, TP at +2%
def simulate_stops(nights, sl=-0.02, tp=0.02):
    res = []
    for d in nights:
        h = np.array(d["hours"])
        # walk forward hour by hour; use maxdn crossing approx: check each hour close vs stop
        val = 0.0; exit_reason = "close"
        for i in range(1, 9):
            r = h[i]
            # worst case: if low crossed stop, exit at stop (approx with path extremes unknown hourly -> use close of hour for conservatism mid: use min(close,prev)... approximate by close)
            if r <= sl:
                val = sl; exit_reason = "sl"; break
            if r >= tp:
                val = tp; exit_reason = "tp"; break
        else:
            val = h[8]
        res.append({"ret": val, "reason": exit_reason})
    r = pd.DataFrame(res)
    return {
        "mean_pct": round(100 * r["ret"].mean(), 3),
        "p_pos": round(100 * (r["ret"] > 0).mean(), 1),
        "mean_kc": round(CAPITAL * r["ret"].mean(), 1),
        "sl_hits": int((r["reason"] == "sl").sum()),
        "tp_hits": int((r["reason"] == "tp").sum()),
        "n": len(r),
    }

df_btc = load("BTC")
n_btc, nights_btc = overnight_stats(df_btc, "BTC")
wd_nights = [d for d in nights_btc if d["dow"] not in ("Saturday", "Sunday")]
we_nights = [d for d in nights_btc if d["dow"] in ("Saturday", "Sunday")]
out["BTC"]["stop_sim"] = {
    "all_sl2_tp2": simulate_stops(nights_btc),
    "weekday_sl2_tp2": simulate_stops(wd_nights),
    "weekend_sl2_tp2": simulate_stops(we_nights),
}

# recent context
btc = load("BTC")
last = btc.iloc[-1]
ret30 = btc["close"].pct_change(24 * 30).iloc[-1]
out["BTC"]["context"] = {
    "last_close": round(float(last["close"]), 0),
    "last_dt": str(btc.index[-1]),
    "ret_30d_pct": round(100 * ret30, 2),
}
# daily realized vol (30d annualized)
d = btc["close"].resample("1D").last().dropna()
dr = d.pct_change().dropna()
out["BTC"]["ann_vol_30d_pct"] = round(100 * dr.tail(30).std() * np.sqrt(365), 1)
out["BTC"]["ann_vol_all_pct"] = round(100 * dr.std() * np.sqrt(365), 1)
# typical daily range last 90 days (high-low)/open
dd = btc.resample("1D").agg({"high": "max", "low": "min", "open": "first"}).dropna()
rng = ((dd["high"] - dd["low"]) / dd["open"]).tail(90)
out["BTC"]["median_daily_range_90d_pct"] = round(100 * rng.median(), 2)

with open("analysis_results.json", "w") as f:
    json.dump(out, f, indent=1)

for name in out:
    print("=====", name)
    for grp, s in out[name]["overnight"].items():
        print(grp, s)
    print("traj:", out[name]["trajectory"])
print("BTC stop:", json.dumps(out["BTC"]["stop_sim"], indent=1))
print("BTC context:", out["BTC"]["context"], "vol30:", out["BTC"]["ann_vol_30d_pct"], "medrange:", out["BTC"]["median_daily_range_90d_pct"])
