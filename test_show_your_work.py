import unittest

from show_your_work import generate_calculation_walkthrough


class TestShowYourWork(unittest.TestCase):
    def test_explanation_contains_run_log_and_details(self):
        results = {
            "company_data": {
                "ticker": "TEST",
                "company_name": "Test Co",
                "current_stock_price": 100.0,
                "shares_outstanding": 10.0,
                "cash": 5.0,
                "total_debt": 8.0,
            },
            "historical_metrics": {
                "ttm_operating_cf": 100.0,
                "ttm_capex": -20.0,
                "ttm_fcf": 80.0,
                "quarterly_fcf": [10.0, 20.0, 30.0, 20.0],
            },
            "historical_data": {
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
                "operating_cash_flow": [30.0, 25.0, 25.0, 20.0],
                "capex": [-5.0, -5.0, -5.0, -5.0],
                "net_income": [10.0, 10.0, 10.0, 10.0],
            },
            "assumptions": {
                "risk_free_rate": 0.04,
                "beta": 1.2,
                "market_risk_premium": 0.06,
                "cost_of_debt": 0.05,
                "tax_rate": 0.21,
                "revenue_growth_rates": [0.05],
                "perpetual_growth_rate": 0.02,
                "esg_adjustment_enabled": True,
                "esg_strength_bps": 50,
            },
            "wacc_results": {
                "cost_of_equity": 0.112,
                "after_tax_cost_debt": 0.0395,
                "equity_weight": 0.7,
                "debt_weight": 0.3,
                "wacc": 0.085,
            },
            "calculation_details": {
                "wacc": {
                    "formula": "WACC = (E/V * Re) + (D/V * Rd * (1-T))",
                    "components": {
                        "market_cap": 1000,
                        "enterprise_value": 1200,
                        "net_debt": 200,
                    },
                },
                "fcf": {
                    "formula": "FCF = Operating Cash Flow - CapEx",
                    "components": {
                        "ttm_operating_cf": 100.0,
                        "ttm_capex": -20.0,
                        "ttm_fcf": 80.0,
                    },
                },
                "terminal_value": {
                    "formula": "TV = FCF(final) * (1 + g) / (WACC - g)",
                    "components": {
                        "final_fcf": 88.0,
                        "growth_rate": 0.02,
                        "wacc": 0.085,
                        "terminal_value": 1200.0,
                    },
                },
                "esg_adjustment": {
                    "strength_bps": 50,
                    "score": 30,
                    "enabled": True,
                    "thresholds": {"good": 20, "bad": 40},
                    "ke_before": 0.112,
                    "ke_after": 0.115,
                    "adjustment": 0.003,
                },
            },
            "projected_fcf": [84.0, 88.0],
            "pv_fcf": [77.0, 75.0],
            "terminal_value": 1200.0,
            "pv_terminal_value": 900.0,
            "enterprise_value_dcf": 1050.0,
            "equity_value": 1047.0,
            "intrinsic_value_per_share": 104.7,
            "current_market_value": 100.0,
            "upside_pct": 4.7,
            "raw_financials": {
                "source": "Alpha Vantage",
                "raw_data": {
                    "cash_from_bs": "5000000",
                    "debt_from_bs": "8000000",
                },
            },
            "data_quality": {
                "quality": "EXCELLENT",
                "issues": [],
                "warnings": [],
            },
            "run_log": [
                {
                    "ts": "2026-01-01T00:00:00Z",
                    "level": "warning",
                    "subsystem": "NEWS",
                    "message": "News API limit",
                }
            ],
            "run_log_summary": {
                "counts": {"info": 1, "warning": 1, "error": 0},
                "total": 2,
            },
        }

        explanation = generate_calculation_walkthrough(results)
        self.assertIn("sections", explanation)
        self.assertTrue(explanation["sections"])
        self.assertIn("run_log", explanation)
        first_item = explanation["sections"][0]["items"][0]
        self.assertIn("tooltip", first_item)
        self.assertIn("details", first_item)


if __name__ == "__main__":
    unittest.main()
