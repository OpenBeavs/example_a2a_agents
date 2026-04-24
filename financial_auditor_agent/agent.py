"""
Financial Auditor Agent
=======================
A Google ADK agent that performs financial analysis: calculates key ratios,
detects anomalies in ledger data, and generates structured audit reports.

No external API keys needed beyond GOOGLE_API_KEY for Gemini.
"""

from __future__ import annotations

import os
import math
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import Agent

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────

def calculate_financial_ratios(
    revenue: float,
    cost_of_goods_sold: float,
    operating_expenses: float,
    net_income: float,
    total_assets: float,
    total_liabilities: float,
    current_assets: float,
    current_liabilities: float,
    equity: float,
) -> dict:
    """Calculate core financial ratios from raw financial statement figures.

    Args:
        revenue: Total revenue / sales for the period.
        cost_of_goods_sold: Direct cost of products/services sold.
        operating_expenses: SG&A and other operating costs (excluding COGS).
        net_income: Bottom-line profit after all expenses and taxes.
        total_assets: Sum of all assets on the balance sheet.
        total_liabilities: Sum of all liabilities on the balance sheet.
        current_assets: Assets convertible to cash within 12 months.
        current_liabilities: Obligations due within 12 months.
        equity: Shareholders' equity (total_assets - total_liabilities).

    Returns:
        dict with 'status' and 'ratios' (a dict of named ratio values with
        brief interpretations) or 'error_message'.
    """
    if revenue <= 0:
        return {"status": "error", "error_message": "Revenue must be positive."}
    if current_liabilities <= 0:
        return {"status": "error", "error_message": "Current liabilities must be positive."}
    if total_assets <= 0:
        return {"status": "error", "error_message": "Total assets must be positive."}

    gross_profit = revenue - cost_of_goods_sold
    gross_margin = round(gross_profit / revenue * 100, 2)
    net_margin = round(net_income / revenue * 100, 2)
    current_ratio = round(current_assets / current_liabilities, 2)
    debt_to_equity = round(total_liabilities / equity, 2) if equity != 0 else None
    roa = round(net_income / total_assets * 100, 2)
    roe = round(net_income / equity * 100, 2) if equity != 0 else None
    operating_ratio = round((cost_of_goods_sold + operating_expenses) / revenue * 100, 2)

    ratios = {
        "gross_margin_pct": {
            "value": gross_margin,
            "interpretation": "Healthy (>40%)" if gross_margin > 40 else "Low (<40%)" if gross_margin < 20 else "Average",
        },
        "net_profit_margin_pct": {
            "value": net_margin,
            "interpretation": "Strong (>15%)" if net_margin > 15 else "Weak (<5%)" if net_margin < 5 else "Adequate",
        },
        "current_ratio": {
            "value": current_ratio,
            "interpretation": "Liquid (>2)" if current_ratio > 2 else "Concern (<1)" if current_ratio < 1 else "Adequate",
        },
        "debt_to_equity": {
            "value": debt_to_equity,
            "interpretation": "High leverage (>2)" if debt_to_equity and debt_to_equity > 2 else "Conservative" if debt_to_equity and debt_to_equity < 1 else "Moderate",
        },
        "return_on_assets_pct": {
            "value": roa,
            "interpretation": "Efficient (>5%)" if roa > 5 else "Inefficient (<2%)" if roa < 2 else "Average",
        },
        "return_on_equity_pct": {
            "value": roe,
            "interpretation": "Excellent (>15%)" if roe and roe > 15 else "Poor (<8%)" if roe and roe < 8 else "Acceptable",
        },
        "operating_ratio_pct": {
            "value": operating_ratio,
            "interpretation": "Efficient (<80%)" if operating_ratio < 80 else "Inefficient (>90%)" if operating_ratio > 90 else "Average",
        },
    }

    return {"status": "success", "ratios": ratios}


def detect_anomalies(
    transaction_amounts: list[float],
    z_score_threshold: float = 2.5,
) -> dict:
    """Detect statistical outliers in a list of transaction amounts using Z-scores.

    Args:
        transaction_amounts: List of numeric transaction values to analyze.
        z_score_threshold: Flag transactions whose |z-score| exceeds this.
                           Standard practice is 2.5–3.0.

    Returns:
        dict with 'status', 'anomalies' list (index + value + z_score),
        'summary' stats, or 'error_message'.
    """
    if len(transaction_amounts) < 3:
        return {"status": "error", "error_message": "Need at least 3 data points."}

    n = len(transaction_amounts)
    mean = sum(transaction_amounts) / n
    variance = sum((x - mean) ** 2 for x in transaction_amounts) / n
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    if std_dev == 0:
        return {
            "status": "success",
            "anomalies": [],
            "summary": {"mean": mean, "std_dev": 0, "message": "All values identical — no anomalies."},
        }

    anomalies = []
    for i, val in enumerate(transaction_amounts):
        z = round((val - mean) / std_dev, 3)
        if abs(z) > z_score_threshold:
            anomalies.append({"index": i, "value": val, "z_score": z})

    return {
        "status": "success",
        "anomalies": anomalies,
        "summary": {
            "n": n,
            "mean": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "threshold": z_score_threshold,
            "anomaly_count": len(anomalies),
        },
    }


def generate_audit_report(
    company_name: str,
    period: str,
    revenue: float,
    net_income: float,
    anomaly_count: int,
    high_risk_ratios: list[str],
) -> dict:
    """Generate a structured audit summary report with risk rating.

    Args:
        company_name: Name of the entity being audited.
        period: Reporting period (e.g. "Q3 2024" or "FY 2023").
        revenue: Total period revenue.
        net_income: Total period net income.
        anomaly_count: Number of flagged anomalous transactions.
        high_risk_ratios: Names of ratios that triggered concern flags.

    Returns:
        dict with 'status' and 'report' dict, or 'error_message'.
    """
    if not company_name.strip():
        return {"status": "error", "error_message": "company_name cannot be empty."}

    risk_score = anomaly_count * 10 + len(high_risk_ratios) * 15
    if risk_score == 0:
        risk_level = "LOW"
        recommendation = "No material findings. Standard monitoring recommended."
    elif risk_score <= 25:
        risk_level = "MEDIUM"
        recommendation = "Minor findings. Increase monitoring frequency."
    else:
        risk_level = "HIGH"
        recommendation = "Significant findings. Immediate management review required."

    return {
        "status": "success",
        "report": {
            "company": company_name,
            "period": period,
            "revenue": revenue,
            "net_income": net_income,
            "profit_margin_pct": round(net_income / revenue * 100, 2) if revenue else 0,
            "anomalous_transactions": anomaly_count,
            "high_risk_ratios": high_risk_ratios,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
        },
    }


# ─────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────

INSTRUCTION = """\
You are a certified Financial Auditor AI. Your job is to analyze financial data,
identify risks, and produce clear audit reports.

Rules:
- Always call the appropriate tool(s) before providing analysis.
- Use `calculate_financial_ratios` when given raw financial figures.
- Use `detect_anomalies` when given a list of transaction amounts.
- Use `generate_audit_report` to summarize findings into a final report.
- Present ratios in a clean table format with risk flags clearly highlighted.
- Flag any ratio or anomaly that indicates potential fraud or mismanagement.
- Decline non-financial questions in one sentence.
"""

root_agent = Agent(
    name="financial_auditor_agent",
    model=os.environ.get("FINANCIAL_AUDITOR_MODEL", "gemini-2.5-flash"),
    description=(
        "A financial auditing agent that calculates key financial ratios, "
        "detects transaction anomalies, and generates structured audit reports."
    ),
    instruction=INSTRUCTION,
    tools=[calculate_financial_ratios, detect_anomalies, generate_audit_report],
)
