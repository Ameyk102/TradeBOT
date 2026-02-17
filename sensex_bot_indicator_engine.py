"""Technical indicator calculations."""

from __future__ import annotations

import logging
from typing import Dict

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD, SMAIndicator

LOGGER = logging.getLogger(__name__)


def _calc_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cumulative_value = (typical_price * df["Volume"]).cumsum()
    cumulative_volume = df["Volume"].replace(0, np.nan).cumsum()
    return cumulative_value / cumulative_volume


def enrich_with_indicators(price_history: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Add RSI, MA, VWAP and MACD indicators for each symbol history."""
    enriched: Dict[str, pd.DataFrame] = {}

    for symbol, df in price_history.items():
        try:
            data = df.copy()
            data["RSI14"] = RSIIndicator(close=data["Close"], window=14).rsi()
            data["SMA20"] = SMAIndicator(close=data["Close"], window=20).sma_indicator()
            data["SMA50"] = SMAIndicator(close=data["Close"], window=50).sma_indicator()
            data["SMA200"] = SMAIndicator(close=data["Close"], window=200).sma_indicator()
            data["EMA20"] = EMAIndicator(close=data["Close"], window=20).ema_indicator()
            data["VWAP"] = _calc_vwap(data)

            macd = MACD(close=data["Close"], window_slow=26, window_fast=12, window_sign=9)
            data["MACD"] = macd.macd()
            data["MACDSignal"] = macd.macd_signal()
            data["MACDHist"] = macd.macd_diff()

            data["Ret1D"] = data["Close"].pct_change()
            data["Ret5D"] = data["Close"].pct_change(5)
            data["VolumeAvg20"] = data["Volume"].rolling(20).mean()
            data["VolumeRatio"] = data["Volume"] / data["VolumeAvg20"]

            enriched[symbol] = data.dropna()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Indicator enrichment failed for %s: %s", symbol, exc)

    return enriched
