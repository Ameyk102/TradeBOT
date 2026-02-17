"""Main orchestration entrypoint for Sensex post-market bot."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from sensex_bot.data_fetcher import collect_market_data
from sensex_bot.indicator_engine import enrich_with_indicators
from sensex_bot.probability_engine import estimate_probability
from sensex_bot.report_generator import (
    build_report_dataframe,
    print_console_report,
    save_excel_report,
    send_email_report,
)
from sensex_bot.risk_engine import batch_evaluate
from sensex_bot.scheduler import start_scheduler
from sensex_bot.signal_generator import generate_signals


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)


def run_daily_analysis(output_dir: Path = Path("output"), email_enabled: bool = False) -> Path:
    """Run full data -> indicators -> signals -> risk -> probability -> report flow."""
    snapshot = collect_market_data(period="1y")
    indicator_data = enrich_with_indicators(snapshot.price_history)

    signals = generate_signals(indicator_data, top_n=10)
    risks = batch_evaluate(signals, indicator_data)
    probabilities = {signal.symbol: estimate_probability(signal, risks[signal.symbol]) for signal in signals}

    report_df = build_report_dataframe(signals, risks, probabilities)
    print_console_report(report_df)

    report_path = output_dir / "sensex_daily_trade_report.xlsx"
    save_excel_report(report_df, report_path)

    if email_enabled:
        send_email_report(
            smtp_host=os.environ["SMTP_HOST"],
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            sender_email=os.environ["SMTP_SENDER"],
            sender_password=os.environ["SMTP_PASSWORD"],
            recipient_email=os.environ["SMTP_RECIPIENT"],
            report_path=report_path,
            subject=f"Sensex Bot Daily Report - {datetime.now().date()}",
        )

    return report_path


def main() -> None:
    mode = os.environ.get("SENSEX_BOT_MODE", "run_once").lower()
    email_enabled = os.environ.get("SENSEX_EMAIL_ENABLED", "false").lower() == "true"

    if mode == "scheduler":
        LOGGER.info("Launching scheduler mode")
        start_scheduler(lambda: run_daily_analysis(email_enabled=email_enabled))
    else:
        LOGGER.info("Launching run-once mode")
        report_path = run_daily_analysis(email_enabled=email_enabled)
        LOGGER.info("Analysis complete. Report: %s", report_path)


if __name__ == "__main__":
    main()
