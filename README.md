# invest

Overnight investing research for small Czech retail amounts (2,000-4,000 Kč) — what actually happens to your money between midnight and 8 AM, backed by 6 months of hourly market data.

## Main report

**[Overnight Investment Research — 7 November 2026](docs/overnight-investment-research-2026-11-07.md)**

- 10 investment options compared (savings, crypto, ETFs, P2P, FX, CFDs, gold)
- Simulated 182 nights of "buy BTC at 0:00 CET, sell at 8:00" with hourly mark-to-market
- Weekend vs weekday night analysis, stop-loss simulations, fee impact at 2,000 Kč
- Czech tax rules for 2026 (crypto 3-year test, ETF exemptions, DAC8)
- 4 charts, all computed from real data

## Repository layout

```
docs/     the full report (Markdown, charts render inline on GitHub)
assets/   charts (PNG)
data/     raw hourly price data (CSV) + computed statistics (JSON)
scripts/  fetch_data.py, analyze.py, charts.js - reproduce everything
```

## Reproduce the analysis

```bash
pip install pandas numpy
python scripts/fetch_data.py    # downloads hourly data from Yahoo Finance
python scripts/analyze.py       # computes overnight statistics
node scripts/charts.js          # renders charts (needs: npm i echarts @resvg/resvg-js)
```

## Key findings (TL;DR)

- An overnight BTC position is a ~48/52 coin flip with an average of **-1.4 Kč per night** on 2,000 Kč (before fees).
- Trading fees (5-48 Kč round trip) exceed the statistical edge at this size.
- Weekend nights are the calmest session (volatility 0.55% vs 0.97% weekday).
- The only option that pays with certainty overnight: a ~4% Czech savings account (+0.19 Kč/night, zero risk).
- Best long-term use of the same money: accumulating S&P 500 UCITS ETF or CZK P2P lending.

*Educational content only - not investment advice. Past performance does not guarantee future results.*
