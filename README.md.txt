# Sensex Daily Post-Market Trading Bot

Automated Python bot for **daily 3:35 PM IST post-market analysis** of Sensex and major NSE stocks using real market data from Yahoo Finance.

## Project Structure

```text
sensex_bot/
├── data_fetcher.py
├── indicator_engine.py
├── signal_generator.py
├── risk_engine.py
├── probability_engine.py
├── report_generator.py
├── scheduler.py
└── main.py
```

## Features

- Collects Sensex constituents + major NSE symbols.
- Computes indicators: RSI, SMA20/50/200, EMA20, VWAP, MACD.
- Identifies top BUY/SELL setups with scoring rules.
- Calculates risk metrics (volatility, drawdown, trend stability, stop-loss).
- Estimates probability of trade success.
- Outputs:
  - Console report
  - Excel file: `output/sensex_daily_trade_report.xlsx`
- Optional SMTP email report delivery.
- Scheduler mode (15:35 IST, Mon-Fri), with holiday check when calendar package is available.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run Once (manual)

```bash
python -m sensex_bot.main
```

## Run Scheduled (APScheduler)

```bash
export SENSEX_BOT_MODE=scheduler
python -m sensex_bot.main
```

## Optional Email Setup

```bash
export SENSEX_EMAIL_ENABLED=true
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_SENDER=you@example.com
export SMTP_PASSWORD=your_app_password
export SMTP_RECIPIENT=recipient@example.com
python -m sensex_bot.main
```

## Cron Setup (Linux/Mac alternative)

Run at 15:35 IST Monday-Friday:

```cron
35 15 * * 1-5 cd /workspace/TradeBOT && /usr/bin/python -m sensex_bot.main >> output/bot.log 2>&1
```

## Windows Task Scheduler (alternative)

1. Create Task → Trigger: Weekly (Mon-Fri), Time: 15:35.
2. Action: Start a program.
3. Program/script: `python`
4. Arguments: `-m sensex_bot.main`
5. Start in: `C:\path\to\TradeBOT`

## Notes

- Data source is real-time/delayed market data from Yahoo Finance.
- Signal logic is rule-based and designed for post-market decision support.
- Not investment advice.
