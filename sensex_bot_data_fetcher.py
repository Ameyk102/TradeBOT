"""Data ingestion layer for the daily Sensex/NSE post-market bot."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)

# Broad liquid symbols to analyze even if Sensex scraping fails.
DEFAULT_NSE_SYMBOLS = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "LT.NS",
    "KOTAKBANK.NS",
    "HCLTECH.NS",
    "ASIANPAINT.NS",
    "AXISBANK.NS",
    "MARUTI.NS",
    "BAJFINANCE.NS",
    "SUNPHARMA.NS",
    "TATAMOTORS.NS",
    "NTPC.NS",
    "POWERGRID.NS",
]


@dataclass
class MarketSnapshot:
    """Container for fetched market data."""

    price_history: Dict[str, pd.DataFrame]
    market_table: pd.DataFrame
    top_gainers: pd.DataFrame
    top_losers: pd.DataFrame
    volume_leaders: pd.DataFrame


def _load_sensex_constituents() -> List[str]:
    """Scrape Sensex constituents from Wikipedia and convert to Yahoo tickers."""
    url = "https://en.wikipedia.org/wiki/BSE_SENSEX"
    try:
        tables = pd.read_html(url)
        # The constituents table has a Symbol/Ticker column (changes over time).
        table = next(
            t
            for t in tables
            if any(col in t.columns for col in ["Symbol", "Ticker", "Companies"])
        )
        symbol_col = "Symbol" if "Symbol" in table.columns else "Ticker"
        symbols = table[symbol_col].dropna().astype(str).str.strip().tolist()
        bo_symbols = [f"{symbol}.BO" for symbol in symbols if symbol]
        LOGGER.info("Loaded %s Sensex constituents from Wikipedia", len(bo_symbols))
        return bo_symbols
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Could not load Sensex constituents from web: %s", exc)
        return []


def _fetch_symbol_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Download OHLCV data for a symbol from Yahoo Finance."""
    df = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    df = df.rename(columns=str.title)
    df.index = pd.to_datetime(df.index)
    return df


def collect_market_data(period: str = "1y") -> MarketSnapshot:
    """Collect historical daily OHLCV for Sensex + liquid NSE stocks.

    Returns a snapshot that includes top gainers/losers and volume leaders based on the
    latest close-versus-previous-close movement.
    """
    universe = sorted(set(_load_sensex_constituents() + DEFAULT_NSE_SYMBOLS))
    if not universe:
        raise RuntimeError("No symbols available for analysis")

    price_history: Dict[str, pd.DataFrame] = {}
    rows = []

    for symbol in universe:
        try:
            hist = _fetch_symbol_history(symbol, period=period)
            hist = hist.dropna(subset=["Close", "Volume"])
            if len(hist) < 60:
                LOGGER.warning("Skipping %s due to insufficient history (%s rows)", symbol, len(hist))
                continue

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            pct_change = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100

            rows.append(
                {
                    "Symbol": symbol,
                    "CurrentPrice": float(latest["Close"]),
                    "PrevClose": float(prev["Close"]),
                    "PctChange": float(pct_change),
                    "Volume": float(latest["Volume"]),
                    "High": float(latest["High"]),
                    "Low": float(latest["Low"]),
                    "Open": float(latest["Open"]),
                }
            )
            price_history[symbol] = hist
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Data fetch failed for %s: %s", symbol, exc)

    market_table = pd.DataFrame(rows).sort_values("PctChange", ascending=False).reset_index(drop=True)
    if market_table.empty:
        raise RuntimeError("Market data collection failed for all symbols")

    top_gainers = market_table.nlargest(10, "PctChange").copy()
    top_losers = market_table.nsmallest(10, "PctChange").copy()
    volume_leaders = market_table.nlargest(10, "Volume").copy()

    LOGGER.info(
        "Market snapshot built: %s symbols, %s gainers, %s losers",
        len(market_table),
        len(top_gainers),
        len(top_losers),
    )

    return MarketSnapshot(
        price_history=price_history,
        market_table=market_table,
        top_gainers=top_gainers,
        top_losers=top_losers,
        volume_leaders=volume_leaders,
    )
