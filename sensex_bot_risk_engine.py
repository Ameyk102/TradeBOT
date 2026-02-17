"""Risk scoring and stop-loss sanity checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from sensex_bot.signal_generator import TradeSignal


@dataclass
class RiskProfile:
    volatility_score: float
    drawdown_risk: float
    trend_stability: float
    stop_loss: float
    risk_level: str


def _risk_level(score: float) -> str:
    if score < 0.33:
        return "LOW"
    if score < 0.66:
        return "MEDIUM"
    return "HIGH"


def evaluate_risk(signal: TradeSignal, data: pd.DataFrame) -> RiskProfile:
    """Compute risk metrics for a given signal."""
    returns = data["Close"].pct_change().dropna()
    volatility = float(returns.std() * np.sqrt(252))

    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = ((cumulative - peak) / peak).min()
    drawdown_abs = abs(float(drawdown))

    trend_strength = abs(float(data["Close"].iloc[-1] / data["Close"].iloc[-30] - 1)) if len(data) >= 30 else 0.0
    trend_stability = max(0.0, min(1.0, 1 - abs(volatility - trend_strength)))

    normalized_vol = min(volatility / 0.6, 1.0)
    normalized_dd = min(drawdown_abs / 0.35, 1.0)
    blended_risk = (normalized_vol * 0.45) + (normalized_dd * 0.45) + ((1 - trend_stability) * 0.10)

    stop_loss = signal.stop_loss
    return RiskProfile(
        volatility_score=round(volatility, 4),
        drawdown_risk=round(drawdown_abs, 4),
        trend_stability=round(trend_stability, 4),
        stop_loss=stop_loss,
        risk_level=_risk_level(blended_risk),
    )


def batch_evaluate(signals: list[TradeSignal], indicator_data: Dict[str, pd.DataFrame]) -> Dict[str, RiskProfile]:
    """Compute risk for all signals."""
    return {signal.symbol: evaluate_risk(signal, indicator_data[signal.symbol]) for signal in signals}
