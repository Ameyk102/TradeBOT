"""Signal generation logic for BUY and SELL candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class TradeSignal:
    symbol: str
    signal: str
    current_price: float
    entry_zone: str
    target_price: float
    stop_loss: float
    reason: str
    signal_score: float


def _buy_score(row: pd.Series) -> float:
    score = 0.0
    score += 20 if row["SMA20"] > row["SMA50"] else 0
    score += 15 if row["SMA50"] > row["SMA200"] else 0
    score += 20 if 40 <= row["RSI14"] <= 70 else 0
    score += 20 if row["MACD"] > row["MACDSignal"] else 0
    score += 15 if row["VolumeRatio"] > 1.2 else 0
    score += min(max(row["Ret5D"] * 100, 0), 10)
    return score


def _sell_score(row: pd.Series) -> float:
    score = 0.0
    score += 20 if row["RSI14"] > 75 else 0
    score += 20 if row["SMA20"] < row["SMA50"] else 0
    score += 15 if row["SMA50"] < row["SMA200"] else 0
    score += 20 if row["MACD"] < row["MACDSignal"] else 0
    score += 15 if row["VolumeRatio"] > 1.2 and row["Ret1D"] < 0 else 0
    score += min(abs(min(row["Ret5D"] * 100, 0)), 10)
    return score


def generate_signals(indicator_data: Dict[str, pd.DataFrame], top_n: int = 10) -> List[TradeSignal]:
    """Create top BUY and SELL candidates from latest indicators."""
    buys: List[TradeSignal] = []
    sells: List[TradeSignal] = []

    for symbol, df in indicator_data.items():
        if df.empty:
            continue
        latest = df.iloc[-1]
        price = float(latest["Close"])

        buy_score = _buy_score(latest)
        sell_score = _sell_score(latest)

        if buy_score >= 55:
            buys.append(
                TradeSignal(
                    symbol=symbol,
                    signal="BUY",
                    current_price=price,
                    entry_zone=f"{price * 0.99:.2f} - {price * 1.01:.2f}",
                    target_price=round(price * 1.05, 2),
                    stop_loss=round(price * 0.97, 2),
                    reason=(
                        f"Momentum + trend alignment (RSI={latest['RSI14']:.1f}, "
                        f"VolRatio={latest['VolumeRatio']:.2f})"
                    ),
                    signal_score=buy_score,
                )
            )

        if sell_score >= 55:
            sells.append(
                TradeSignal(
                    symbol=symbol,
                    signal="SELL",
                    current_price=price,
                    entry_zone=f"{price * 0.99:.2f} - {price * 1.01:.2f}",
                    target_price=round(price * 0.95, 2),
                    stop_loss=round(price * 1.03, 2),
                    reason=(
                        f"Reversal risk elevated (RSI={latest['RSI14']:.1f}, "
                        f"MACDHist={latest['MACDHist']:.3f})"
                    ),
                    signal_score=sell_score,
                )
            )

    buys = sorted(buys, key=lambda x: x.signal_score, reverse=True)[:top_n]
    sells = sorted(sells, key=lambda x: x.signal_score, reverse=True)[:top_n]
    return buys + sells
#Commit from Vivek