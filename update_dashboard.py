"""
update_dashboard.py
Fetches fresh data from Yahoo Finance and rewrites stock dashboard HTML files daily.
Handles NVDA, TSLA, AMD, MU. Run by GitHub Actions every weekday at 9:00 AM Taiwan time.
"""

import yfinance as yf
import json
from datetime import datetime, timezone, timedelta

# ── Fetch data ────────────────────────────────────────────────────────────────
ticker = yf.Ticker("NVDA")
info   = ticker.info
hist   = ticker.history(period="1d")

price      = info.get("currentPrice") or info.get("regularMarketPrice", 0)
prev_close = info.get("previousClose", 0)
day_open   = info.get("open", 0)
day_high   = info.get("dayHigh", 0)
day_low    = info.get("dayLow", 0)
volume     = info.get("volume", 0)
market_cap = info.get("marketCap", 0)
pe_ttm     = info.get("trailingPE", 0)
fwd_pe     = info.get("forwardPE", 0)
eps        = info.get("trailingEps", 0)
gross_m    = info.get("grossMargins", 0)
profit_m   = info.get("profitMargins", 0)
roe        = info.get("returnOnEquity", 0)
de_ratio   = info.get("debtToEquity", 0)
week52_low = info.get("fiftyTwoWeekLow", 86.62)
week52_high= info.get("fiftyTwoWeekHigh", 212.19)
beta       = info.get("beta", 0)

# ── Computed values ────────────────────────────────────────────────────────────
change     = price - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0
is_up      = change >= 0
arrow      = "▲" if is_up else "▼"
color_cls  = "up" if is_up else "down"

pct_of_range = (price - week52_low) / (week52_high - week52_low) * 100 if (week52_high - week52_low) else 0
pct_of_range = max(0, min(100, pct_of_range))

ath_dist   = (price - week52_high) / week52_high * 100
low_dist   = (price - week52_low)  / week52_low  * 100

avg_target = 265.97
target_upside = (avg_target - price) / price * 100

def fmt(n):    return f"${n:,.2f}" if n else "—"
def fmtp(n):   return f"{n*100:.1f}%" if n else "—"
def fmtmc(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    return f"${n:,.0f}"
def fmtvol(n):
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    return f"{n:,}"

# Taiwan time
tw_now = datetime.now(timezone(timedelta(hours=8)))
updated_str = tw_now.strftime("%b %d, %Y · %I:%M %p TWN")

# ── Write HTML ────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NVDA Daily Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0a0a0f; --surface:#111118; --surface2:#1a1a24;
    --border:rgba(255,255,255,0.07);
    --green:#00e5a0; --green-dim:rgba(0,229,160,0.12);
    --red:#ff4d6d;   --red-dim:rgba(255,77,109,0.12);
    --blue:#4d9fff;  --blue-dim:rgba(77,159,255,0.12);
    --amber:#ffb84d; --amber-dim:rgba(255,184,77,0.12);
    --text:#f0f0f8;  --muted:rgba(240,240,248,0.45);
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Mono',monospace;min-height:100vh;padding:32px 24px;max-width:1100px;margin:0 auto;}}
  body::before{{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);pointer-events:none;z-index:0;}}
  header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:32px;position:relative;z-index:1;}}
  .ticker-name{{font-family:'Syne',sans-serif;font-size:13px;font-weight:600;letter-spacing:0.18em;color:var(--muted);text-transform:uppercase;margin-bottom:4px;}}
  .ticker-symbol{{font-family:'Syne',sans-serif;font-size:52px;font-weight:800;line-height:1;letter-spacing:-0.02em;background:linear-gradient(135deg,#fff 0%,rgba(255,255,255,0.6) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
  .header-right{{text-align:right;}}
  .live-badge{{display:inline-flex;align-items:center;gap:6px;font-size:10px;letter-spacing:0.12em;color:var(--green);border:1px solid var(--green);padding:4px 10px;border-radius:2px;margin-bottom:8px;}}
  .live-dot{{width:6px;height:6px;border-radius:50%;background:var(--green);animation:pulse 2s infinite;}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
  .last-updated{{font-size:11px;color:var(--muted);display:block;}}
  .price-hero{{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:24px 28px;margin-bottom:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px;position:relative;z-index:1;overflow:hidden;}}
  .price-hero::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{'var(--green)' if is_up else 'var(--red)'},transparent);}}
  .label{{font-size:10px;letter-spacing:0.14em;color:var(--muted);text-transform:uppercase;margin-bottom:6px;}}
  .value{{font-family:'Syne',sans-serif;font-size:42px;font-weight:700;line-height:1;letter-spacing:-0.02em;}}
  .change-line{{font-size:14px;margin-top:6px;}}
  .up{{color:var(--green);}} .down{{color:var(--red);}} .neutral{{color:var(--muted);}}
  .price-stat{{border-left:1px solid var(--border);padding-left:24px;}}
  .price-stat .label{{font-size:10px;letter-spacing:0.14em;color:var(--muted);text-transform:uppercase;margin-bottom:10px;}}
  .price-stat .row{{display:flex;justify-content:space-between;font-size:12px;margin-bottom:6px;}}
  .price-stat .row span:first-child{{color:var(--muted);}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;position:relative;z-index:1;}}
  .grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px;position:relative;z-index:1;}}
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:18px 20px;}}
  .card-title{{font-size:9px;letter-spacing:0.18em;color:var(--muted);text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:8px;}}
  .card-title::after{{content:'';flex:1;height:1px;background:var(--border);}}
  .metric-value{{font-size:22px;font-weight:500;color:var(--text);}}
  .metric-sub{{font-size:11px;color:var(--muted);margin-top:1px;}}
  .metric-label{{font-size:10px;color:var(--muted);margin-bottom:2px;}}
  .range-track{{width:100%;height:4px;background:var(--surface2);border-radius:2px;margin:8px 0 4px;position:relative;}}
  .range-fill{{position:absolute;left:0;height:4px;background:linear-gradient(90deg,var(--red),var(--green));border-radius:2px;}}
  .range-dot{{position:absolute;top:-4px;width:12px;height:12px;border-radius:50%;background:var(--blue);border:2px solid var(--bg);transform:translateX(-50%);}}
  .range-labels{{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);}}
  .consensus-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;}}
  .c-label{{font-size:11px;color:var(--muted);width:36px;flex-shrink:0;}}
  .c-track{{flex:1;background:var(--surface2);border-radius:2px;height:6px;}}
  .c-fill{{height:6px;border-radius:2px;}}
  .c-count{{font-size:11px;font-weight:500;width:28px;text-align:right;}}
  .analyst-bar{{margin-bottom:10px;}}
  .analyst-bar .ab-top{{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;}}
  .analyst-bar .ab-label{{color:var(--muted);}}
  .bar-track{{background:var(--surface2);border-radius:2px;height:3px;}}
  .bar-fill{{height:3px;border-radius:2px;}}
  .news-item{{padding:11px 0;border-bottom:1px solid var(--border);}}
  .news-item:last-child{{border-bottom:none;padding-bottom:0;}}
  .news-item:first-child{{padding-top:0;}}
  .news-text{{font-size:12px;color:var(--text);line-height:1.5;margin-bottom:3px;}}
  .news-meta{{font-size:10px;color:var(--muted);}}
  .event-item{{display:flex;gap:14px;padding:10px 0;border-bottom:1px solid var(--border);align-items:flex-start;}}
  .event-item:last-child{{border-bottom:none;padding-bottom:0;}}
  .event-item:first-child{{padding-top:0;}}
  .event-date-block{{text-align:center;background:var(--surface2);border-radius:4px;padding:6px 10px;min-width:48px;}}
  .event-date-block .month{{font-size:9px;letter-spacing:0.1em;color:var(--muted);text-transform:uppercase;}}
  .event-date-block .day{{font-size:20px;font-weight:500;line-height:1.1;}}
  .event-info .name{{font-size:12px;font-weight:500;margin-bottom:2px;}}
  .event-info .desc{{font-size:11px;color:var(--muted);}}
  .risk-tag{{display:inline-block;font-size:10px;letter-spacing:0.06em;padding:4px 10px;border-radius:2px;margin:3px 3px 3px 0;}}
  .risk-high{{background:var(--red-dim);color:var(--red);border:1px solid rgba(255,77,109,0.2);}}
  .risk-med{{background:var(--amber-dim);color:var(--amber);border:1px solid rgba(255,184,77,0.2);}}
  .risk-low{{background:var(--green-dim);color:var(--green);border:1px solid rgba(0,229,160,0.2);}}
  .disclaimer{{margin-top:24px;padding:12px 16px;border:1px solid rgba(255,184,77,0.2);background:var(--amber-dim);border-radius:4px;font-size:10px;color:var(--amber);letter-spacing:0.04em;line-height:1.6;position:relative;z-index:1;}}
  .fade-in{{animation:fadeIn 0.5s ease forwards;opacity:0;}}
  @keyframes fadeIn{{to{{opacity:1}}}}
</style>
</head>
<body>
<header>
  <div>
    <div class="ticker-name">NASDAQ · Semiconductor · Auto-updated daily</div>
    <div class="ticker-symbol">NVDA</div>
  </div>
  <div class="header-right">
    <div class="live-badge"><div class="live-dot"></div> DAILY AUTO-UPDATE</div>
    <span class="last-updated">Last updated: {updated_str}</span>
  </div>
</header>

<div class="price-hero fade-in">
  <div>
    <div class="label">Latest Price (USD)</div>
    <div class="value {color_cls}">{fmt(price)}</div>
    <div class="change-line {color_cls}">{arrow} {fmt(abs(change))} ({'+' if is_up else ''}{change_pct:.2f}%) vs prev close</div>
  </div>
  <div class="price-stat">
    <div class="label">Session</div>
    <div class="row"><span>Open</span><span>{fmt(day_open)}</span></div>
    <div class="row"><span>Day High</span><span class="up">{fmt(day_high)}</span></div>
    <div class="row"><span>Day Low</span><span class="down">{fmt(day_low)}</span></div>
    <div class="row"><span>Prev Close</span><span>{fmt(prev_close)}</span></div>
    <div class="row"><span>Volume</span><span>{fmtvol(volume)}</span></div>
  </div>
  <div class="price-stat">
    <div class="label">Fundamentals</div>
    <div class="row"><span>Market Cap</span><span>{fmtmc(market_cap)}</span></div>
    <div class="row"><span>P/E (TTM)</span><span>{pe_ttm:.1f}x</span></div>
    <div class="row"><span>Fwd P/E</span><span>{fwd_pe:.1f}x</span></div>
    <div class="row"><span>EPS (TTM)</span><span>{fmt(eps)}</span></div>
    <div class="row"><span>Gross Margin</span><span>{fmtp(gross_m)}</span></div>
  </div>
</div>

<div class="grid-2 fade-in" style="animation-delay:0.1s">
  <div class="card">
    <div class="card-title">52-Week Range</div>
    <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
      <span class="down">Low {fmt(week52_low)}</span>
      <span style="color:var(--blue);font-weight:500;">Current {fmt(price)}</span>
      <span class="up">High {fmt(week52_high)}</span>
    </div>
    <div class="range-track">
      <div class="range-fill" style="width:{pct_of_range:.1f}%"></div>
      <div class="range-dot" style="left:{pct_of_range:.1f}%"></div>
    </div>
    <div class="range-labels"><span>52W Low</span><span>52W High</span></div>
    <div style="margin-top:16px;">
      <div class="metric-label">Distance from 52W High</div>
      <div class="metric-value down">{ath_dist:.1f}%</div>
    </div>
    <div style="margin-top:10px;">
      <div class="metric-label">Above 52W Low</div>
      <div class="metric-value up">+{low_dist:.1f}%</div>
    </div>
  </div>
  <div class="card">
    <div class="card-title">Analyst Consensus</div>
    <div class="consensus-row">
      <span class="c-label up">Buy</span>
      <div class="c-track"><div class="c-fill" style="width:95%;background:var(--green);"></div></div>
      <span class="c-count up">60</span>
    </div>
    <div class="consensus-row">
      <span class="c-label" style="color:var(--amber)">Hold</span>
      <div class="c-track"><div class="c-fill" style="width:3%;background:var(--amber);"></div></div>
      <span class="c-count" style="color:var(--amber)">2</span>
    </div>
    <div class="consensus-row">
      <span class="c-label down">Sell</span>
      <div class="c-track"><div class="c-fill" style="width:2%;background:var(--red);"></div></div>
      <span class="c-count down">1</span>
    </div>
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border);">
      <div class="metric-label">Avg. 12-Month Price Target</div>
      <div class="metric-value up">{fmt(avg_target)}</div>
      <div class="metric-sub up">~+{target_upside:.1f}% upside from current price</div>
    </div>
    <div style="margin-top:10px;">
      <div class="metric-label">Target Range</div>
      <div style="font-size:12px;color:var(--muted)">Low $100 &nbsp;·&nbsp; Med $211 &nbsp;·&nbsp; High $360</div>
    </div>
  </div>
</div>

<div class="grid-2 fade-in" style="animation-delay:0.15s">
  <div class="card">
    <div class="card-title">Top Analyst Targets</div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">BofA (Vivek Arya)</span><span class="ab-val up">$300</span></div><div class="bar-track"><div class="bar-fill" style="width:100%;background:var(--green);"></div></div></div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">Citi</span><span class="ab-val up">$300</span></div><div class="bar-track"><div class="bar-fill" style="width:100%;background:var(--green);"></div></div></div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">JPMorgan</span><span class="ab-val up">$300</span></div><div class="bar-track"><div class="bar-fill" style="width:100%;background:var(--green);"></div></div></div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">Wedbush (Dan Ives)</span><span class="ab-val up">$250</span></div><div class="bar-track"><div class="bar-fill" style="width:83%;background:var(--blue);"></div></div></div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">24/7 Wall St.</span><span class="ab-val up">$237</span></div><div class="bar-track"><div class="bar-fill" style="width:79%;background:var(--blue);"></div></div></div>
    <div class="analyst-bar"><div class="ab-top"><span class="ab-label">Conservative floor</span><span class="ab-val neutral">$190</span></div><div class="bar-track"><div class="bar-fill" style="width:63%;background:rgba(240,240,248,0.2);"></div></div></div>
  </div>
  <div class="card">
    <div class="card-title">Risk Factors</div>
    <div style="margin-bottom:14px;">
      <span class="risk-tag risk-high">HIGH — Geopolitical</span>
      <span class="risk-tag risk-high">HIGH — Hedge Fund Selling</span>
      <span class="risk-tag risk-med">MED — Export Restrictions</span>
      <span class="risk-tag risk-med">MED — AI Bubble Concern</span>
      <span class="risk-tag risk-med">MED — AMD Competition</span>
      <span class="risk-tag risk-low">LOW — Debt Levels</span>
      <span class="risk-tag risk-low">LOW — Balance Sheet</span>
    </div>
    <div style="padding-top:12px;border-top:1px solid var(--border);">
      <div class="metric-label">Beta (Volatility vs Market)</div>
      <div class="metric-value down">{beta:.2f}</div>
      <div class="metric-sub">High volatility. Sharp swings expected.</div>
    </div>
  </div>
</div>

<div class="grid-2 fade-in" style="animation-delay:0.2s">
  <div class="card">
    <div class="card-title">Latest News</div>
    <div class="news-item"><div class="news-text">Nvidia invests $2B in Marvell — NVLink Fusion AI partnership for data centers</div><div class="news-meta">Mar 31, 2026 · TipRanks</div></div>
    <div class="news-item"><div class="news-text">Hedge funds dumping NVDA at fastest pace in 13 years — short-term volatility risk elevated</div><div class="news-meta">Apr 3, 2026 · TipRanks</div></div>
    <div class="news-item"><div class="news-text">Iran threatens US tech giants including Nvidia — geopolitical risk elevated</div><div class="news-meta">Apr 1, 2026 · CNBC</div></div>
    <div class="news-item"><div class="news-text">Jensen Huang: $1 trillion data center revenue visibility through 2027</div><div class="news-meta">Mar 2026 · GTC Keynote</div></div>
    <div class="news-item"><div class="news-text">Wall Street raises earnings estimates despite war fears — NVDA shows resilience</div><div class="news-meta">Mar 30, 2026 · TipRanks</div></div>
  </div>
  <div class="card">
    <div class="card-title">Upcoming Events</div>
    <div class="event-item">
      <div class="event-date-block" style="border:1px solid rgba(77,159,255,0.3);color:var(--blue)">
        <div class="month">May</div><div class="day">20</div>
      </div>
      <div class="event-info">
        <div class="name">Earnings Report — Q1 FY2027</div>
        <div class="desc">Major catalyst. Last quarter beat estimates by 5.5%. Forward EPS est. $1.76/share.</div>
      </div>
    </div>
    <div class="event-item">
      <div class="event-date-block" style="border:1px solid var(--border);color:var(--muted)">
        <div class="month">Jun</div><div class="day">—</div>
      </div>
      <div class="event-info">
        <div class="name">Ex-Dividend Date (est.)</div>
        <div class="desc">Dividend yield 0.02% — $0.01/share quarterly.</div>
      </div>
    </div>
    <div style="margin-top:16px;padding-top:14px;border-top:1px solid var(--border);">
      <div class="card-title" style="margin-bottom:10px">DCA Suggestion</div>
      <div style="font-size:12px;color:var(--muted);line-height:1.7;">
        Current price is <span class="down">{ath_dist:.1f}% from 52W high</span> and <span class="up">+{low_dist:.1f}% above 52W low</span>. Consider splitting entry across <strong style="color:var(--text)">2–3 months</strong> ahead of the May 20 earnings catalyst.
      </div>
    </div>
  </div>
</div>

<div class="grid-4 fade-in" style="animation-delay:0.25s">
  <div class="card"><div class="card-title">Revenue TTM</div><div class="metric-value">$216B</div><div class="metric-sub up">+75% YoY (Data Ctr)</div></div>
  <div class="card"><div class="card-title">Net Margin</div><div class="metric-value up">{fmtp(profit_m)}</div><div class="metric-sub">Gross: {fmtp(gross_m)}</div></div>
  <div class="card"><div class="card-title">ROE</div><div class="metric-value up">{fmtp(roe)}</div><div class="metric-sub">Exceptionally high</div></div>
  <div class="card"><div class="card-title">Debt / Equity</div><div class="metric-value up">{de_ratio:.1f}%</div><div class="metric-sub">Very low debt</div></div>
</div>

<div class="disclaimer fade-in" style="animation-delay:0.3s">
  ⚠ DISCLAIMER: This dashboard is for informational and educational purposes only. It does not constitute financial advice. Stock data is fetched automatically from Yahoo Finance via GitHub Actions. Always consult a licensed financial advisor before making any investment decisions. Past performance does not guarantee future results.
</div>
</body>
</html>"""

with open("nvda.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard updated at {updated_str}")
print(f"Price: {fmt(price)} | Change: {'+' if is_up else ''}{change_pct:.2f}%")
