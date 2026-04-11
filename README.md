# 📈 NVDA Daily Dashboard

A self-updating stock dashboard for **NVIDIA (NVDA)** published on GitHub Pages.

🔗 **Live site:** https://carterlin.github.io/nvda-dashboard

---

## What it does

- Fetches live NVDA price data from Yahoo Finance every weekday at **9:00 AM Taiwan time**
- Automatically rebuilds `index.html` with fresh data
- Commits and pushes the update to GitHub Pages
- No server needed — runs entirely on **GitHub Actions** (free)

## What's auto-updated daily
- Current price, open, high, low, volume
- Change vs previous close
- 52-week range position
- P/E ratio, EPS, market cap, margins
- Upside % to analyst price target

## What's manually updated (ask Claude for a refresh)
- Analyst targets and ratings
- News headlines
- Risk factors
- Upcoming events

---

## Repo structure

```
nvda-dashboard/
├── index.html              # The dashboard (auto-rebuilt daily)
├── update_dashboard.py     # Python script that fetches data + writes HTML
├── .github/
│   └── workflows/
│       └── update-dashboard.yml   # GitHub Actions schedule
└── README.md
```

## Setup

1. Fork or clone this repo
2. Go to **Settings → Pages** → Deploy from `main` branch `/root`
3. GitHub Actions will run automatically every weekday at 9 AM TWN
4. To trigger manually: **Actions → Update NVDA Dashboard Daily → Run workflow**

## Run locally

```bash
pip install yfinance requests
python update_dashboard.py
open index.html
```

---

> ⚠️ This dashboard is for informational purposes only and is not financial advice. Always consult a licensed financial advisor before making investment decisions.
