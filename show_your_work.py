"""
Generate step-by-step DCF calculation walkthroughs for students.
"""


def generate_calculation_walkthrough(results):
    """Return a structured explanation of key DCF steps."""
    results = results or {}
    company = results.get("company_data", {})
    hist = results.get("historical_metrics", {})
    assumptions = results.get("assumptions", {})
    wacc_results = results.get("wacc_results", {})

    growth_rates = assumptions.get("revenue_growth_rates") or []
    projected_items = []
    for i, fcf in enumerate(results.get("projected_fcf", [])):
        if i < len(growth_rates):
            explanation = f"Uses growth rate of {growth_rates[i]:.1%}."
        elif growth_rates:
            explanation = "Uses the final growth rate."
        else:
            explanation = "No growth rate provided."

        projected_items.append({
            "label": f"Year {i + 1} Projected FCF",
            "value": f"${fcf:.1f}M",
            "explanation": explanation
        })

    sections = [
        {
            "title": "Step 1: Gather Company Data",
            "items": [
                {
                    "label": "Company Name",
                    "value": company.get("company_name"),
                    "explanation": "The company we are analyzing."
                },
                {
                    "label": "Current Stock Price",
                    "value": f"${company.get('current_stock_price', 0):.2f}",
                    "explanation": "What the market thinks the stock is worth today."
                },
                {
                    "label": "Shares Outstanding",
                    "value": f"{company.get('shares_outstanding', 0):.1f}M",
                    "explanation": "Total number of shares in existence."
                },
            ],
        },
        {
            "title": "Step 2: Calculate Free Cash Flow",
            "formula": "FCF = Operating Cash Flow - CapEx",
            "items": [
                {
                    "label": "Operating Cash Flow (TTM)",
                    "value": f"${hist.get('ttm_operating_cf', 0):.1f}M",
                    "explanation": "Cash generated from core business operations."
                },
                {
                    "label": "Capital Expenditures (TTM)",
                    "value": f"${hist.get('ttm_capex', 0):.1f}M",
                    "explanation": "Cash spent on equipment, buildings, and long-term assets."
                },
                {
                    "label": "Free Cash Flow (TTM)",
                    "value": f"${hist.get('ttm_fcf', 0):.1f}M",
                    "calculation": f"${hist.get('ttm_operating_cf', 0):.1f}M + (${hist.get('ttm_capex', 0):.1f}M)",
                    "explanation": "Cash available to investors after maintaining the business."
                },
            ],
        },
        {
            "title": "Step 3: Calculate WACC (Discount Rate)",
            "formula": "WACC = (E/V * Re) + (D/V * Rd * (1-T))",
            "items": [
                {
                    "label": "Cost of Equity (Re)",
                    "value": f"{wacc_results.get('cost_of_equity', 0):.2%}",
                    "calculation": (
                        f"Rf({assumptions.get('risk_free_rate', 0):.2%}) "
                        f"+ Beta({assumptions.get('beta', 0):.2f}) "
                        f"* MRP({assumptions.get('market_risk_premium', 0):.2%})"
                    ),
                    "explanation": "Return shareholders expect for the risk they take."
                },
                {
                    "label": "After-Tax Cost of Debt",
                    "value": f"{wacc_results.get('after_tax_cost_debt', 0):.2%}",
                    "calculation": (
                        f"{assumptions.get('cost_of_debt', 0):.2%} "
                        f"* (1 - {assumptions.get('tax_rate', 0):.2%})"
                    ),
                    "explanation": "Cost of debt after tax deductions."
                },
                {
                    "label": "WACC",
                    "value": f"{wacc_results.get('wacc', 0):.2%}",
                    "calculation": (
                        f"({wacc_results.get('equity_weight', 0):.2f} * {wacc_results.get('cost_of_equity', 0):.2%}) "
                        f"+ ({wacc_results.get('debt_weight', 0):.2f} * {wacc_results.get('after_tax_cost_debt', 0):.2%})"
                    ),
                    "explanation": "Blended cost of capital from equity and debt."
                },
            ],
        },
        {
            "title": "Step 4: Project Future Cash Flows",
            "explanation": "We project future cash flows based on growth assumptions.",
            "items": projected_items,
        },
        {
            "title": "Step 5: Discount to Present Value",
            "formula": "PV = FV / (1 + WACC)^n",
            "explanation": "Convert future cash flows to today's dollars.",
            "items": [
                {
                    "label": f"Year {i + 1} Present Value",
                    "value": f"${pv:.1f}M",
                    "explanation": "Discounted using the WACC rate."
                }
                for i, pv in enumerate(results.get("pv_fcf", []))
            ],
        },
        {
            "title": "Step 6: Terminal Value",
            "formula": "TV = FCF(Year 6) / (WACC - g)",
            "items": [
                {
                    "label": "Terminal Value",
                    "value": f"${results.get('terminal_value', 0):.1f}M",
                    "explanation": "Value of all cash flows beyond the forecast period."
                },
                {
                    "label": "PV of Terminal Value",
                    "value": f"${results.get('pv_terminal_value', 0):.1f}M",
                    "explanation": "Terminal value discounted to today."
                },
            ],
        },
        {
            "title": "Step 7: Intrinsic Value",
            "items": [
                {
                    "label": "Enterprise Value",
                    "value": f"${results.get('enterprise_value_dcf', 0):.1f}M",
                    "explanation": "Sum of discounted cash flows and terminal value."
                },
                {
                    "label": "Equity Value",
                    "value": f"${results.get('equity_value', 0):.1f}M",
                    "calculation": (
                        f"${results.get('enterprise_value_dcf', 0):.1f}M "
                        f"- ${company.get('total_debt', 0):.1f}M "
                        f"+ ${company.get('cash', 0):.1f}M"
                    ),
                    "explanation": "Enterprise value adjusted for debt and cash."
                },
                {
                    "label": "Intrinsic Value Per Share",
                    "value": f"${results.get('intrinsic_value_per_share', 0):.2f}",
                    "calculation": (
                        f"${results.get('equity_value', 0):.1f}M / "
                        f"{company.get('shares_outstanding', 0):.1f}M shares"
                    ),
                    "explanation": "Value per share implied by DCF."
                },
            ],
        },
    ]

    return {
        "sections": sections,
        "key_assumptions": {
            "Growth Rates": assumptions.get("revenue_growth_rates", []),
            "Perpetual Growth": f"{assumptions.get('perpetual_growth_rate', 0):.1%}",
            "Tax Rate": f"{assumptions.get('tax_rate', 0):.1%}",
            "Risk-Free Rate": f"{assumptions.get('risk_free_rate', 0):.1%}",
            "Market Risk Premium": f"{assumptions.get('market_risk_premium', 0):.1%}",
        },
        "final_verdict": {
            "intrinsic_value": f"${results.get('intrinsic_value_per_share', 0):.2f}",
            "market_price": f"${company.get('current_stock_price', 0):.2f}",
            "upside": f"{results.get('upside_pct', 0):.1f}%",
            "recommendation": (
                "BUY" if results.get("upside_pct", 0) > 15
                else ("HOLD" if results.get("upside_pct", 0) > -10 else "SELL")
            ),
        },
    }
