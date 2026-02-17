"""Console + Excel reporting."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

from sensex_bot.probability_engine import ProbabilityEstimate
from sensex_bot.risk_engine import RiskProfile
from sensex_bot.signal_generator import TradeSignal

LOGGER = logging.getLogger(__name__)


def build_report_dataframe(
    signals: Iterable[TradeSignal],
    risks: Dict[str, RiskProfile],
    probabilities: Dict[str, ProbabilityEstimate],
) -> pd.DataFrame:
    rows = []
    for signal in signals:
        risk = risks[signal.symbol]
        prob = probabilities[signal.symbol]
        rows.append(
            {
                "Stock Name": signal.symbol,
                "Signal (BUY/SELL)": signal.signal,
                "Current Price": round(signal.current_price, 2),
                "Entry Zone": signal.entry_zone,
                "Target Price": signal.target_price,
                "Stop Loss": risk.stop_loss,
                "Risk Level": risk.risk_level,
                "Probability (%)": prob.probability,
                "Reason": f"{signal.reason} | {prob.confidence_note}",
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["Signal (BUY/SELL)", "Probability (%)"], ascending=[True, False])
    return df


def print_console_report(report_df: pd.DataFrame) -> None:
    print("\n" + "=" * 110)
    print(f"SENSEX/NSE POST-MARKET ACTIONABLE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 110)
    if report_df.empty:
        print("No actionable signals today.")
        return
    print(report_df.to_string(index=False))


def save_excel_report(report_df: pd.DataFrame, output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="Signals", index=False)

    LOGGER.info("Excel report saved to %s", output_path)
    return output_path


def send_email_report(
    smtp_host: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    report_path: Path,
    subject: Optional[str] = None,
) -> None:
    """Optional SMTP mailer for report attachment."""
    import smtplib
    from email.message import EmailMessage

    subject = subject or f"Daily Sensex Trade Report - {datetime.now().date()}"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message.set_content("Attached is your daily Sensex trade report.")

    with open(report_path, "rb") as file:
        content = file.read()
        message.add_attachment(
            content,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=report_path.name,
        )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

    LOGGER.info("Email report sent to %s", recipient_email)
