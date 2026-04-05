"""
update_dashboard.py
Fetches fresh data from Yahoo Finance for all 6 stocks and writes data.json.
HTML pages load data.json via JavaScript on startup — no HTML patching needed.
Run by GitHub Actions every weekday at 9:00 AM Taiwan time.
"""

import json
import yfinance as yf
from datetime import datetime, timezone, timedelta

STOCKS = ["NVDA", "TSLA", "AMD", "MU", "AVGO", "MRVL"]
TW = timezone(timedelta(hours=8))


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_market_cap(n):
    if not n: return "—"
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    return f"${n:,.0f}"

def fmt_revenue(n):
    if not n: return "—"
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    return f"${n/1e6:.0f}M"

def fmt_pe(n):
    if not n or n <= 0: return "虧損"
    return f"{n:.1f}x"

def fmt_eps(n):
    if n is None: return "—"
    sign = "" if n >= 0 else "-"
    return f"{sign}${abs(n):.2f}"

def fmt_pct(n):
    if not n: return "—"
    return f"{n*100:.1f}%"

def fmt_debt_equity(n):
    if not n: return "—"
    return f"{n:.1f}%"

def fmt_dividend(n):
    if not n: return "—"
    return f"{n*100:.1f}%"

def fmt_beta(n):
    if not n: return "—"
    return f"{n:.2f}"

def fmt_price(n):
    if not n: return "—"
    return f"${n:,.2f}"


# ── Main ──────────────────────────────────────────────────────────────────────

output = {"updated": datetime.now(TW).strftime("%Y-%m-%d %H:%M TWN"), "stocks": {}}
errors = []

for symbol in STOCKS:
    print(f"\n{'─'*40}")
    print(f"Fetching {symbol}...")

    try:
        info = yf.Ticker(symbol).info

        low52      = info.get("fiftyTwoWeekLow", 0)
        high52     = info.get("fiftyTwoWeekHigh", 0)
        avg_target = info.get("targetMeanPrice", 0)

        print(f"  52W: {low52:.2f} – {high52:.2f}  |  Target: {avg_target}")

        output["stocks"][symbol] = {
            # Formatted strings for display (matched to data-yf attribute names)
            "marketCap":    fmt_market_cap(info.get("marketCap")),
            "trailingPE":   fmt_pe(info.get("trailingPE")),
            "forwardPE":    fmt_pe(info.get("forwardPE")),
            "eps":          fmt_eps(info.get("trailingEps")),
            "grossMargin":  fmt_pct(info.get("grossMargins")),
            "revenue":      fmt_revenue(info.get("totalRevenue")),
            "beta":         fmt_beta(info.get("beta")),
            "debtEquity":   fmt_debt_equity(info.get("debtToEquity")),
            "dividendYield":fmt_dividend(info.get("dividendYield")),
            "targetPrice":  fmt_price(avg_target) if avg_target else None,
            # Raw numbers for JS range bar and upside % calculation
            "low52":      round(low52, 2),
            "high52":     round(high52, 2),
            "avgTarget":  round(avg_target, 2),
        }
        print(f"  OK")

    except Exception as e:
        errors.append(f"{symbol}: {e}")
        print(f"  FAIL: {e}")

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

tw_now = datetime.now(TW).strftime("%Y-%m-%d %H:%M TWN")
print(f"\n{'='*40}")
print(f"data.json written at {tw_now}")
print(f"Stocks: {list(output['stocks'].keys())}")
if errors:
    print(f"Errors: {'; '.join(errors)}")
