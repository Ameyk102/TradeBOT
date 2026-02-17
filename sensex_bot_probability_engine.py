"""Probability estimation for trade success."""

from __future__ import annotations

from dataclasses import dataclass

from sensex_bot.risk_engine import RiskProfile
from sensex_bot.signal_generator import TradeSignal


@dataclass
class ProbabilityEstimate:
    probability: float
    confidence_note: str


def estimate_probability(signal: TradeSignal, risk: RiskProfile) -> ProbabilityEstimate:
    """Estimate trade success probability based on indicator/risk alignment.

    Heuristic model with weighted features:
    - signal score
    - risk profile
    - trend stability
    """
    signal_component = min(signal.signal_score / 100, 1.0)
    risk_component = {"LOW": 0.85, "MEDIUM": 0.65, "HIGH": 0.45}[risk.risk_level]
    stability_component = risk.trend_stability

    score = (signal_component * 0.55) + (risk_component * 0.30) + (stability_component * 0.15)
    probability = round(score * 100, 2)

    if probability >= 70:
        note = "Strong trend continuation"
    elif probability >= 55:
        note = "Moderate edge with controlled risk"
    else:
        note = "Weak setup; position sizing caution"

    return ProbabilityEstimate(probability=probability, confidence_note=note)
