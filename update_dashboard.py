"""
update_dashboard.py
Fetches fresh data from Yahoo Finance and updates dynamic values in all stock HTML files.
Preserves existing HTML structure — only patches data-yf marked elements and JS constants.
Run by GitHub Actions every weekday at 9:00 AM Taiwan time.
"""

import re
import yfinance as yf
from datetime import datetime, timezone, timedelta

STOCKS = {
    "NVDA": "nvda.html",
    "TSLA": "tsla.html",
    "AMD":  "amd.html",
    "MU":   "mu.html",
    "AVGO": "avgo.html",
    "MRVL": "mrvl.html",
}

TW = timezone(timedelta(hours=8))


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_market_cap(n):
    if not n:
        return "—"
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.1f}B"
    return f"${n:,.0f}"

def fmt_revenue(n):
    if not n:
        return "—"
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.1f}B"
    return f"${n/1e6:.0f}M"

def fmt_pe(n):
    if not n or n <= 0:
        return "虧損"
    return f"{n:.1f}x"

def fmt_eps(n):
    if n is None:
        return "—"
    sign = "" if n >= 0 else "-"
    return f"{sign}${abs(n):.2f}"

def fmt_pct(n):
    if not n:
        return "—"
    return f"{n*100:.1f}%"

def fmt_debt_equity(n):
    if not n:
        return "—"
    # yfinance returns debtToEquity as a ratio (e.g. 5.4 means 5.4%)
    return f"{n:.1f}%"

def fmt_dividend(n):
    if not n:
        return "—"
    return f"{n*100:.1f}%"

def fmt_beta(n):
    if not n:
        return "—"
    return f"{n:.2f}"

def fmt_price(n):
    if not n:
        return "—"
    return f"${n:,.2f}"


# ── Patch helpers ─────────────────────────────────────────────────────────────

def patch_data_yf(html, field, new_value):
    """Replace inner text of <... data-yf="field">OLD<"""
    pattern = rf'((?:<[^>]*\s)?data-yf="{re.escape(field)}"[^>]*>)[^<]*(<)'
    return re.sub(pattern, rf'\g<1>{new_value}\2', html)

def patch_span_id(html, span_id, new_value):
    """Replace inner text of <span id="span_id">OLD</span>"""
    pattern = rf'(<span[^>]*\bid="{re.escape(span_id)}"[^>]*>)[^<]*(</span>)'
    return re.sub(pattern, rf'\g<1>{new_value}\2', html)

def patch_js_constants(html, low52, high52, avg_target):
    """Update the JS const LOW52=...,HIGH52=...,AVG_TARGET=...; line"""
    pattern = r'const LOW52=[\d.]+,HIGH52=[\d.]+,AVG_TARGET=[\d.]+;'
    replacement = f'const LOW52={low52:.2f},HIGH52={high52:.2f},AVG_TARGET={avg_target:.2f};'
    return re.sub(pattern, replacement, html)


# ── Main ──────────────────────────────────────────────────────────────────────

updated = []
errors = []

for symbol, filename in STOCKS.items():
    print(f"\n{'─'*40}")
    print(f"Fetching {symbol}...")

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        market_cap   = info.get("marketCap")
        trailing_pe  = info.get("trailingPE")
        forward_pe   = info.get("forwardPE")
        eps          = info.get("trailingEps")
        gross_margin = info.get("grossMargins")
        revenue      = info.get("totalRevenue")
        beta         = info.get("beta")
        debt_equity  = info.get("debtToEquity")
        dividend     = info.get("dividendYield")
        low52        = info.get("fiftyTwoWeekLow", 0)
        high52       = info.get("fiftyTwoWeekHigh", 0)
        avg_target   = info.get("targetMeanPrice", 0)

        print(f"  Price: {info.get('currentPrice') or info.get('regularMarketPrice')}")
        print(f"  52W: {low52:.2f} - {high52:.2f}")
        print(f"  Target: {avg_target}")
        print(f"  P/E TTM: {trailing_pe}  Fwd P/E: {forward_pe}")

        with open(filename, "r", encoding="utf-8") as f:
            html = f.read()

        # Patch metric grid values
        html = patch_data_yf(html, "marketCap",    fmt_market_cap(market_cap))
        html = patch_data_yf(html, "trailingPE",   fmt_pe(trailing_pe))
        html = patch_data_yf(html, "forwardPE",    fmt_pe(forward_pe))
        html = patch_data_yf(html, "eps",          fmt_eps(eps))
        html = patch_data_yf(html, "grossMargin",  fmt_pct(gross_margin))
        html = patch_data_yf(html, "revenue",      fmt_revenue(revenue))
        html = patch_data_yf(html, "beta",         fmt_beta(beta))
        html = patch_data_yf(html, "debtEquity",   fmt_debt_equity(debt_equity))
        html = patch_data_yf(html, "dividendYield",fmt_dividend(dividend))

        # Patch analyst target display
        if avg_target:
            html = patch_data_yf(html, "targetPrice", fmt_price(avg_target))

        # Patch 52W range display spans
        if low52:
            html = patch_span_id(html, "low52",  f"低 {fmt_price(low52)}")
        if high52:
            html = patch_span_id(html, "high52", f"高 {fmt_price(high52)}")

        # Patch JS constants (used by range bar + upside % calculation)
        if low52 and high52 and avg_target:
            html = patch_js_constants(html, low52, high52, avg_target)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        updated.append(symbol)
        print(f"  OK {filename} updated")

    except Exception as e:
        errors.append(f"{symbol}: {e}")
        print(f"  FAIL Error: {e}")

# ── Summary ───────────────────────────────────────────────────────────────────
tw_now = datetime.now(TW).strftime("%Y-%m-%d %H:%M TWN")
print(f"\n{'='*40}")
print(f"Completed at {tw_now}")
print(f"Updated: {', '.join(updated) if updated else 'none'}")
if errors:
    print(f"Errors:  {'; '.join(errors)}")
