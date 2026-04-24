"""Tests for financial_auditor_agent tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from financial_auditor_agent.tools import (
    calculate_financial_ratios,
    detect_anomalies,
    generate_audit_report,
)


class TestCalculateFinancialRatios:
    def _base_kwargs(self, **overrides):
        defaults = dict(
            revenue=1_000_000,
            cost_of_goods_sold=400_000,
            operating_expenses=200_000,
            net_income=150_000,
            total_assets=800_000,
            total_liabilities=300_000,
            current_assets=250_000,
            current_liabilities=100_000,
            equity=500_000,
        )
        defaults.update(overrides)
        return defaults

    def test_success_returns_all_ratios(self):
        result = calculate_financial_ratios(**self._base_kwargs())
        assert result["status"] == "success"
        ratios = result["ratios"]
        assert "gross_margin_pct" in ratios
        assert "net_profit_margin_pct" in ratios
        assert "current_ratio" in ratios
        assert "return_on_assets_pct" in ratios

    def test_gross_margin_calculation(self):
        result = calculate_financial_ratios(**self._base_kwargs(
            revenue=1_000_000, cost_of_goods_sold=600_000
        ))
        assert result["status"] == "success"
        assert result["ratios"]["gross_margin_pct"]["value"] == 40.0

    def test_current_ratio_calculation(self):
        result = calculate_financial_ratios(**self._base_kwargs(
            current_assets=300_000, current_liabilities=150_000
        ))
        assert result["status"] == "success"
        assert result["ratios"]["current_ratio"]["value"] == 2.0

    def test_net_margin_calculation(self):
        result = calculate_financial_ratios(**self._base_kwargs(
            revenue=1_000_000, net_income=200_000
        ))
        assert result["status"] == "success"
        assert result["ratios"]["net_profit_margin_pct"]["value"] == 20.0

    def test_zero_revenue_returns_error(self):
        result = calculate_financial_ratios(**self._base_kwargs(revenue=0))
        assert result["status"] == "error"

    def test_zero_current_liabilities_returns_error(self):
        result = calculate_financial_ratios(**self._base_kwargs(current_liabilities=0))
        assert result["status"] == "error"

    def test_ratio_interpretations_present(self):
        result = calculate_financial_ratios(**self._base_kwargs())
        for ratio in result["ratios"].values():
            assert "interpretation" in ratio


class TestDetectAnomalies:
    def test_detects_obvious_outlier(self):
        data = [100, 110, 105, 108, 99, 103, 50_000, 107]
        result = detect_anomalies(data)
        assert result["status"] == "success"
        assert len(result["anomalies"]) >= 1
        values = [a["value"] for a in result["anomalies"]]
        assert 50_000 in values

    def test_no_anomalies_in_uniform_data(self):
        data = [100.0] * 20
        result = detect_anomalies(data)
        assert result["status"] == "success"
        assert result["anomalies"] == []

    def test_threshold_respected(self):
        data = [10, 12, 11, 13, 100, 11, 10]
        result_tight = detect_anomalies(data, z_score_threshold=1.0)
        result_loose = detect_anomalies(data, z_score_threshold=3.0)
        assert len(result_tight["anomalies"]) >= len(result_loose["anomalies"])

    def test_too_few_points_returns_error(self):
        result = detect_anomalies([1, 2])
        assert result["status"] == "error"

    def test_summary_fields_present(self):
        data = [1, 2, 3, 4, 5, 100]
        result = detect_anomalies(data)
        assert "summary" in result
        assert "mean" in result["summary"]
        assert "std_dev" in result["summary"]

    def test_anomaly_index_is_accurate(self):
        # Use a threshold of 2.0 so 9999 in a dataset of ~50s is clearly flagged
        data = [50, 52, 49, 51, 9999, 50, 53]
        result = detect_anomalies(data, z_score_threshold=2.0)
        anomaly_indices = [a["index"] for a in result["anomalies"]]
        assert 4 in anomaly_indices


class TestGenerateAuditReport:
    def test_low_risk_report(self):
        result = generate_audit_report(
            company_name="Good Corp",
            period="Q1 2024",
            revenue=1_000_000,
            net_income=200_000,
            anomaly_count=0,
            high_risk_ratios=[],
        )
        assert result["status"] == "success"
        assert result["report"]["risk_level"] == "LOW"

    def test_medium_risk_report(self):
        result = generate_audit_report(
            company_name="Mid Corp",
            period="Q2 2024",
            revenue=500_000,
            net_income=10_000,
            anomaly_count=1,
            high_risk_ratios=["current_ratio"],
        )
        assert result["status"] == "success"
        assert result["report"]["risk_level"] == "MEDIUM"

    def test_high_risk_report(self):
        result = generate_audit_report(
            company_name="Risk Corp",
            period="Q3 2024",
            revenue=200_000,
            net_income=-50_000,
            anomaly_count=5,
            high_risk_ratios=["gross_margin", "current_ratio", "debt_to_equity"],
        )
        assert result["status"] == "success"
        assert result["report"]["risk_level"] == "HIGH"

    def test_profit_margin_calculated(self):
        result = generate_audit_report(
            company_name="Acme",
            period="FY 2023",
            revenue=1_000_000,
            net_income=150_000,
            anomaly_count=0,
            high_risk_ratios=[],
        )
        assert result["report"]["profit_margin_pct"] == 15.0

    def test_empty_company_name_returns_error(self):
        result = generate_audit_report(
            company_name="   ",
            period="Q1",
            revenue=100_000,
            net_income=10_000,
            anomaly_count=0,
            high_risk_ratios=[],
        )
        assert result["status"] == "error"

    def test_report_contains_recommendation(self):
        result = generate_audit_report(
            company_name="Test Co",
            period="Q4 2024",
            revenue=1_000_000,
            net_income=50_000,
            anomaly_count=0,
            high_risk_ratios=[],
        )
        assert "recommendation" in result["report"]
        assert len(result["report"]["recommendation"]) > 0
