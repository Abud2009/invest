# -*- coding: utf-8 -*-
"""Fetch hourly data for BTC, ETH, gold, EURUSD from Yahoo Finance and save to CSV."""
import json, urllib.request, ssl, time

SYMBOLS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "GOLD": "GC=F",
    "EURUSD": "EURUSD=X",
    "SPX": "^GSPC",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for name, sym in SYMBOLS.items():
    interval = "1h" if name in ("BTC", "ETH", "GOLD", "EURUSD") else "1d"
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval={interval}&range=6mo")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data = json.loads(r.read().decode())
        res = data["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        rows = []
        for i, t in enumerate(ts):
            o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
            if c is None:
                continue
            rows.append(f"{t},{o},{h},{l},{c}")
        fn = f"data_{name}.csv"
        with open(fn, "w") as f:
            f.write("timestamp,open,high,low,close\n" + "\n".join(rows))
        print(name, sym, "rows:", len(rows), "->", fn)
    except Exception as e:
        print(name, sym, "FAILED:", e)
    time.sleep(1)
