"""
Generate step-by-step DCF calculation walkthroughs for students.
"""


def _fmt_money(value, decimals=1, suffix="M"):
    if value is None:
        return "N/A"
    try:
        return f"${value:.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_price(value, decimals=2):
    if value is None:
        return "N/A"
    try:
        return f"${value:.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_pct(value, decimals=2):
    if value is None:
        return "N/A"
    try:
        return f"{value:.{decimals}%}"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_shares(value, decimals=1):
    if value is None:
        return "N/A"
    try:
        return f"{value:.{decimals}f}M"
    except (TypeError, ValueError):
        return "N/A"


def _provenance(source, raw_field=None, raw_value=None, normalization=None):
    return {
        "source": source,
        "raw_field": raw_field,
        "raw_value": raw_value,
        "normalization": normalization,
    }


def _item(label, value, explanation, tooltip=None, calculation=None, details=None):
    return {
        "label": label,
        "value": value,
        "explanation": explanation,
        "tooltip": tooltip or explanation,
        "calculation": calculation,
        "details": details or {},
    }


def _table(title, columns, rows):
    return {
        "title": title,
        "columns": columns,
        "rows": rows,
    }


def generate_calculation_walkthrough(results):
    """Return a structured explanation of key DCF steps."""
    results = results or {}
    company = results.get("company_data", {})
    hist = results.get("historical_metrics", {})
    hist_data = results.get("historical_data", {})
    assumptions = results.get("assumptions", {})
    wacc_results = results.get("wacc_results", {})
    calc_details = results.get("calculation_details", {})
    wacc_details = calc_details.get("wacc", {})
    wacc_components = wacc_details.get("components", {})
    fcf_details = calc_details.get("fcf", {})
    terminal_details = calc_details.get("terminal_value", {})
    esg_details = calc_details.get("esg_adjustment", {})
    raw_financials = results.get("raw_financials", {})
    data_sources = results.get("data_sources", {})
    run_timestamp = results.get("run_timestamp")
    run_log = results.get("run_log", [])
    run_log_summary = results.get("run_log_summary", {})

    company_source = raw_financials.get("source") or data_sources.get("company_data") or "Unknown"
    beta_source = data_sources.get("beta") or "Unknown"

    price_raw_field = (
        "Alpha Vantage GLOBAL_QUOTE: 05. price"
        if company_source == "Alpha Vantage"
        else "yfinance info.currentPrice/regularMarketPrice"
    )
    shares_raw_field = (
        "Alpha Vantage OVERVIEW: SharesOutstanding"
        if company_source == "Alpha Vantage"
        else "yfinance info.sharesOutstanding"
    )

    cash_raw = raw_financials.get("raw_data", {}).get("cash_from_bs")
    debt_raw = raw_financials.get("raw_data", {}).get("debt_from_bs")

    growth_rates = assumptions.get("revenue_growth_rates") or []
    projected_fcf = results.get("projected_fcf", [])
    pv_fcf = results.get("pv_fcf", [])

    sections = []

    sections.append({
        "title": "Step 0: Run Context & Data Quality",
        "items": [
            _item(
                "Ticker",
                company.get("ticker", "N/A"),
                "Ticker symbol used for this run.",
                details={
                    "formula": None,
                    "inputs": {"ticker": company.get("ticker")},
                    "intermediate": {},
                    "provenance": _provenance("User input", "ticker", company.get("ticker"), "none"),
                },
            ),
            _item(
                "Company Name",
                company.get("company_name", "N/A"),
                "Company name resolved from the data source.",
                details={
                    "formula": None,
                    "inputs": {"company_name": company.get("company_name")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, "company_name", company.get("company_name"), "none"),
                },
            ),
            _item(
                "Run Timestamp",
                run_timestamp or "N/A",
                "When this valuation run was generated.",
                details={
                    "formula": None,
                    "inputs": {"run_timestamp": run_timestamp},
                    "intermediate": {},
                    "provenance": _provenance("System", "run_timestamp", run_timestamp, "ISO 8601 UTC"),
                },
            ),
            _item(
                "Data Quality",
                results.get("data_quality", {}).get("quality", "N/A"),
                "Summary of data completeness checks.",
                details={
                    "formula": None,
                    "inputs": {
                        "issues": results.get("data_quality", {}).get("issues", []),
                        "warnings": results.get("data_quality", {}).get("warnings", []),
                    },
                    "intermediate": {},
                    "provenance": _provenance("DataQualityChecker", "data_quality", results.get("data_quality"), "rules-based"),
                },
            ),
            _item(
                "Run Log Summary",
                f"{run_log_summary.get('counts', {})}",
                "Counts of info, warning, and error events captured during the run.",
                details={
                    "formula": None,
                    "inputs": run_log_summary,
                    "intermediate": {},
                    "provenance": _provenance("Run Log", "run_log_summary", run_log_summary, "event aggregation"),
                },
            ),
        ],
    })

    sections.append({
        "title": "Step 1: Inputs & Data Sources",
        "items": [
            _item(
                "Current Stock Price",
                _fmt_price(company.get("current_stock_price")),
                "Market price used for upside/downside calculations.",
                details={
                    "formula": None,
                    "inputs": {"price": company.get("current_stock_price")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, price_raw_field, company.get("current_stock_price"), "none"),
                },
            ),
            _item(
                "Shares Outstanding",
                _fmt_shares(company.get("shares_outstanding")),
                "Total shares outstanding in millions.",
                details={
                    "formula": None,
                    "inputs": {"shares_outstanding": company.get("shares_outstanding")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, shares_raw_field, company.get("shares_outstanding"), "shares to millions"),
                },
            ),
            _item(
                "Cash",
                _fmt_money(company.get("cash")),
                "Cash and equivalents used to adjust enterprise value.",
                details={
                    "formula": None,
                    "inputs": {"cash": company.get("cash")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, "balance_sheet.cash", cash_raw, "USD to millions"),
                },
            ),
            _item(
                "Total Debt",
                _fmt_money(company.get("total_debt")),
                "Total debt used to adjust enterprise value.",
                details={
                    "formula": None,
                    "inputs": {"total_debt": company.get("total_debt")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, "balance_sheet.totalDebt", debt_raw, "USD to millions"),
                },
            ),
            _item(
                "Risk-Free Rate",
                _fmt_pct(assumptions.get("risk_free_rate")),
                "Baseline return used in CAPM.",
                details={
                    "formula": None,
                    "inputs": {"risk_free_rate": assumptions.get("risk_free_rate")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "risk_free_rate", assumptions.get("risk_free_rate"), "decimal to percent"),
                },
            ),
            _item(
                "Beta",
                f"{assumptions.get('beta', 0):.2f}" if assumptions.get("beta") is not None else "N/A",
                "Sensitivity of the stock to market moves.",
                details={
                    "formula": None,
                    "inputs": {"beta": assumptions.get("beta")},
                    "intermediate": {},
                    "provenance": _provenance(beta_source, "beta", assumptions.get("beta"), "none"),
                },
            ),
            _item(
                "Market Risk Premium",
                _fmt_pct(assumptions.get("market_risk_premium")),
                "Expected market return above the risk-free rate.",
                details={
                    "formula": None,
                    "inputs": {"market_risk_premium": assumptions.get("market_risk_premium")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "market_risk_premium", assumptions.get("market_risk_premium"), "decimal to percent"),
                },
            ),
            _item(
                "Cost of Debt",
                _fmt_pct(assumptions.get("cost_of_debt")),
                "Pre-tax cost of debt used in WACC.",
                details={
                    "formula": None,
                    "inputs": {"cost_of_debt": assumptions.get("cost_of_debt")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "cost_of_debt", assumptions.get("cost_of_debt"), "decimal to percent"),
                },
            ),
            _item(
                "Tax Rate",
                _fmt_pct(assumptions.get("tax_rate")),
                "Tax rate used to adjust the cost of debt.",
                details={
                    "formula": None,
                    "inputs": {"tax_rate": assumptions.get("tax_rate")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "tax_rate", assumptions.get("tax_rate"), "decimal to percent"),
                },
            ),
            _item(
                "ESG Adjustment Enabled",
                "Yes" if assumptions.get("esg_adjustment_enabled", True) else "No",
                "Whether ESG scores modify the cost of equity.",
                details={
                    "formula": None,
                    "inputs": {"esg_adjustment_enabled": assumptions.get("esg_adjustment_enabled")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "esg_adjustment_enabled", assumptions.get("esg_adjustment_enabled"), "boolean"),
                },
            ),
            _item(
                "ESG Strength (bps)",
                f"{assumptions.get('esg_strength_bps', 0)} bps",
                "Max basis-point adjustment applied to cost of equity.",
                details={
                    "formula": None,
                    "inputs": {"esg_strength_bps": assumptions.get("esg_strength_bps")},
                    "intermediate": {},
                    "provenance": _provenance("Assumption", "esg_strength_bps", assumptions.get("esg_strength_bps"), "basis points"),
                },
            ),
        ],
    })

    quarters = hist_data.get("quarters", [])
    ocf = hist_data.get("operating_cash_flow", [])
    capex = hist_data.get("capex", [])
    net_income = hist_data.get("net_income", [])
    fcf_series = hist.get("quarterly_fcf", [])

    if quarters:
        start = max(0, len(quarters) - 4)
        rows = []
        for i in range(start, len(quarters)):
            rows.append([
                quarters[i],
                _fmt_money(ocf[i]),
                _fmt_money(capex[i]),
                _fmt_money(fcf_series[i] if i < len(fcf_series) else None),
                _fmt_money(net_income[i] if i < len(net_income) else None),
            ])
    else:
        rows = []

    sections.append({
        "title": "Step 2: Historical Cash Flows (TTM)",
        "formula": "FCF = Operating Cash Flow - CapEx",
        "items": [
            _item(
                "Operating Cash Flow (TTM)",
                _fmt_money(hist.get("ttm_operating_cf")),
                "Total operating cash flow for the trailing twelve months.",
                calculation=None,
                details={
                    "formula": fcf_details.get("formula"),
                    "inputs": {"operating_cash_flow": hist.get("ttm_operating_cf")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, "cash_flow.operating_cash_flow", hist.get("ttm_operating_cf"), "USD to millions"),
                },
            ),
            _item(
                "Capital Expenditures (TTM)",
                _fmt_money(hist.get("ttm_capex")),
                "Capital expenditures for the trailing twelve months.",
                details={
                    "formula": fcf_details.get("formula"),
                    "inputs": {"capex": hist.get("ttm_capex")},
                    "intermediate": {},
                    "provenance": _provenance(company_source, "cash_flow.capex", hist.get("ttm_capex"), "USD to millions"),
                },
            ),
            _item(
                "Free Cash Flow (TTM)",
                _fmt_money(hist.get("ttm_fcf")),
                "Free cash flow used as the base for projections.",
                calculation=f"{_fmt_money(hist.get('ttm_operating_cf'))} + ({_fmt_money(hist.get('ttm_capex'))})",
                details={
                    "formula": fcf_details.get("formula"),
                    "inputs": fcf_details.get("components", {}),
                    "intermediate": {},
                    "provenance": _provenance(company_source, "cash_flow.ttm_fcf", hist.get("ttm_fcf"), "USD to millions"),
                },
            ),
        ],
        "tables": [
            _table(
                "Last 4 Quarters",
                ["Quarter", "Operating CF", "CapEx", "Free Cash Flow", "Net Income"],
                rows,
            )
        ] if rows else [],
    })

    sections.append({
        "title": "Step 3: WACC (Discount Rate)",
        "formula": "WACC = (E/V * Re) + (D/V * Rd * (1-T))",
        "items": [
            _item(
                "Cost of Equity (Re)",
                _fmt_pct(wacc_results.get("cost_of_equity")),
                "Return required by equity investors (CAPM).",
                calculation=(
                    f"Rf({_fmt_pct(assumptions.get('risk_free_rate'))}) + "
                    f"Beta({assumptions.get('beta', 0):.2f}) * "
                    f"MRP({_fmt_pct(assumptions.get('market_risk_premium'))})"
                ),
                details={
                    "formula": "Ke = Rf + Beta * MRP",
                    "inputs": {
                        "risk_free_rate": assumptions.get("risk_free_rate"),
                        "beta": assumptions.get("beta"),
                        "market_risk_premium": assumptions.get("market_risk_premium"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "CAPM", None, "decimal to percent"),
                },
            ),
            _item(
                "After-Tax Cost of Debt",
                _fmt_pct(wacc_results.get("after_tax_cost_debt")),
                "Cost of debt after tax deductions.",
                calculation=f"{_fmt_pct(assumptions.get('cost_of_debt'))} * (1 - {_fmt_pct(assumptions.get('tax_rate'))})",
                details={
                    "formula": "Rd(after tax) = Rd * (1 - Tax Rate)",
                    "inputs": {
                        "cost_of_debt": assumptions.get("cost_of_debt"),
                        "tax_rate": assumptions.get("tax_rate"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "after_tax_cost_debt", wacc_results.get("after_tax_cost_debt"), "decimal to percent"),
                },
            ),
            _item(
                "Equity Weight (E/V)",
                f"{wacc_results.get('equity_weight', 0):.2f}" if wacc_results.get("equity_weight") is not None else "N/A",
                "Proportion of capital financed by equity.",
                details={
                    "formula": "Equity Weight = Market Cap / Enterprise Value",
                    "inputs": {
                        "market_cap": wacc_components.get("market_cap"),
                        "enterprise_value": wacc_components.get("enterprise_value"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "equity_weight", wacc_results.get("equity_weight"), "ratio"),
                },
            ),
            _item(
                "Debt Weight (D/V)",
                f"{wacc_results.get('debt_weight', 0):.2f}" if wacc_results.get("debt_weight") is not None else "N/A",
                "Proportion of capital financed by debt.",
                details={
                    "formula": "Debt Weight = Net Debt / Enterprise Value",
                    "inputs": {
                        "net_debt": wacc_components.get("net_debt"),
                        "enterprise_value": wacc_components.get("enterprise_value"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "debt_weight", wacc_results.get("debt_weight"), "ratio"),
                },
            ),
            _item(
                "ESG Adjustment (bps)",
                f"{esg_details.get('strength_bps', 0)} bps" if esg_details else "N/A",
                "Basis-point adjustment applied based on ESG score.",
                details={
                    "formula": "ESG adjustment varies between +/- strength based on score thresholds",
                    "inputs": {
                        "score": esg_details.get("score"),
                        "enabled": esg_details.get("enabled"),
                        "thresholds": esg_details.get("thresholds"),
                    },
                    "intermediate": {
                        "ke_before": esg_details.get("ke_before"),
                        "ke_after": esg_details.get("ke_after"),
                        "adjustment": esg_details.get("adjustment"),
                    },
                    "provenance": _provenance("ESG Adjuster", "esg_adjustment", esg_details.get("score"), "basis points"),
                },
            ),
            _item(
                "WACC",
                _fmt_pct(wacc_results.get("wacc")),
                "Blended cost of capital used to discount cash flows.",
                calculation=(
                    f"({wacc_results.get('equity_weight', 0):.2f} * {_fmt_pct(wacc_results.get('cost_of_equity'))}) + "
                    f"({wacc_results.get('debt_weight', 0):.2f} * {_fmt_pct(wacc_results.get('after_tax_cost_debt'))})"
                ),
                details={
                    "formula": wacc_details.get("formula"),
                    "inputs": wacc_components,
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "wacc", wacc_results.get("wacc"), "decimal to percent"),
                },
            ),
        ],
    })

    stress = results.get("stress_test", {})
    projected_items = []
    for i, fcf in enumerate(projected_fcf):
        growth = growth_rates[i] if i < len(growth_rates) else (growth_rates[-1] if growth_rates else None)
        projected_items.append(
            _item(
                f"Year {i + 1} Projected FCF",
                _fmt_money(fcf),
                "Projected free cash flow based on growth assumptions.",
                tooltip="Projected FCF with the chosen growth rate.",
                calculation=None,
                details={
                    "formula": "FCF(year) = FCF(prior) * (1 + growth)",
                    "inputs": {
                        "growth_rate": growth,
                        "prior_fcf": projected_fcf[i - 1] if i > 0 else hist.get("ttm_fcf"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", f"projected_fcf[{i}]", fcf, "USD to millions"),
                },
            )
        )

    stress_tables = []
    if stress.get("enabled") and stress.get("base_projected_fcf"):
        rows = []
        base_series = stress.get("base_projected_fcf", [])
        stressed_series = stress.get("stressed_projected_fcf", [])
        carbon_costs = stress.get("carbon_costs", [])
        for i, base_value in enumerate(base_series):
            stressed_value = stressed_series[i] if i < len(stressed_series) else None
            carbon_cost = carbon_costs[i] if i < len(carbon_costs) else None
            rows.append([
                f"Year {i + 1}",
                _fmt_money(base_value),
                _fmt_money(stressed_value),
                _fmt_money(carbon_cost, suffix="") if carbon_cost is not None else "N/A",
            ])
        stress_tables.append(
            _table(
                "Stress Test: Base vs Stressed FCF",
                ["Year", "Base FCF", "Stressed FCF", "Carbon Cost"],
                rows,
            )
        )

    sections.append({
        "title": "Step 4: Forecast Free Cash Flows",
        "explanation": "Projected cash flows for the explicit forecast period.",
        "items": projected_items,
        "tables": stress_tables,
    })

    discount_items = []
    for i, pv in enumerate(pv_fcf):
        year = i + 1
        discount_items.append(
            _item(
                f"Year {year} Present Value",
                _fmt_money(pv),
                "Discounted cash flow for the year.",
                calculation=f"FCF / (1 + WACC)^{year}",
                details={
                    "formula": "PV = FCF / (1 + WACC)^n",
                    "inputs": {
                        "fcf": projected_fcf[i] if i < len(projected_fcf) else None,
                        "wacc": wacc_results.get("wacc"),
                        "year": year,
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", f"pv_fcf[{i}]", pv, "USD to millions"),
                },
            )
        )

    sections.append({
        "title": "Step 5: Discount to Present Value",
        "formula": "PV = FV / (1 + WACC)^n",
        "explanation": "Convert future cash flows to today's dollars.",
        "items": discount_items,
    })

    sections.append({
        "title": "Step 6: Terminal Value",
        "formula": "TV = FCF(final) * (1 + g) / (WACC - g)",
        "items": [
            _item(
                "Terminal Value",
                _fmt_money(results.get("terminal_value")),
                "Value of cash flows beyond the explicit forecast period.",
                details={
                    "formula": terminal_details.get("formula"),
                    "inputs": terminal_details.get("components", {}),
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "terminal_value", results.get("terminal_value"), "USD to millions"),
                },
            ),
            _item(
                "PV of Terminal Value",
                _fmt_money(results.get("pv_terminal_value")),
                "Terminal value discounted back to today.",
                details={
                    "formula": "PV(TV) = TV / (1 + WACC)^n",
                    "inputs": {
                        "terminal_value": results.get("terminal_value"),
                        "wacc": wacc_results.get("wacc"),
                        "years": len(projected_fcf),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "pv_terminal_value", results.get("pv_terminal_value"), "USD to millions"),
                },
            ),
        ],
    })

    sections.append({
        "title": "Step 7: Equity Value and Per-Share Value",
        "items": [
            _item(
                "Enterprise Value",
                _fmt_money(results.get("enterprise_value_dcf")),
                "Sum of discounted cash flows and terminal value.",
                details={
                    "formula": "EV = sum(PV FCF) + PV(TV)",
                    "inputs": {
                        "pv_fcf": pv_fcf,
                        "pv_terminal_value": results.get("pv_terminal_value"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "enterprise_value_dcf", results.get("enterprise_value_dcf"), "USD to millions"),
                },
            ),
            _item(
                "Equity Value",
                _fmt_money(results.get("equity_value")),
                "Enterprise value adjusted for debt and cash.",
                calculation=f"EV - Debt + Cash",
                details={
                    "formula": "Equity Value = Enterprise Value - Debt + Cash",
                    "inputs": {
                        "enterprise_value": results.get("enterprise_value_dcf"),
                        "total_debt": company.get("total_debt"),
                        "cash": company.get("cash"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "equity_value", results.get("equity_value"), "USD to millions"),
                },
            ),
            _item(
                "Intrinsic Value Per Share",
                _fmt_price(results.get("intrinsic_value_per_share")),
                "Equity value divided by shares outstanding.",
                calculation=f"Equity Value / Shares Outstanding",
                details={
                    "formula": "Intrinsic Value = Equity Value / Shares Outstanding",
                    "inputs": {
                        "equity_value": results.get("equity_value"),
                        "shares_outstanding": company.get("shares_outstanding"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "intrinsic_value_per_share", results.get("intrinsic_value_per_share"), "USD per share"),
                },
            ),
            _item(
                "Upside/Downside",
                _fmt_pct(results.get("upside_pct", 0) / 100 if results.get("upside_pct") is not None else None, decimals=1),
                "Percent difference between intrinsic value and market price.",
                details={
                    "formula": "(Intrinsic - Price) / Price",
                    "inputs": {
                        "intrinsic_value_per_share": results.get("intrinsic_value_per_share"),
                        "current_price": company.get("current_stock_price"),
                    },
                    "intermediate": {},
                    "provenance": _provenance("Calculation", "upside_pct", results.get("upside_pct"), "percent"),
                },
            ),
        ],
    })

    sensitivity = results.get("sensitivity", {})
    if sensitivity.get("matrix"):
        matrix_rows = []
        for row in sensitivity.get("matrix", []):
            matrix_rows.append([
                _fmt_price(value) if value is not None else "N/A" for value in row
            ])

        sections.append({
            "title": "Optional: Sensitivity Matrix",
            "items": [],
            "tables": [
                _table(
                    "Sensitivity: WACC vs Terminal Growth",
                    [" "] + [f"{g:.2%}" for g in sensitivity.get("growth_range", [])],
                    [
                        [f"{w:.2%}"] + row
                        for w, row in zip(sensitivity.get("wacc_range", []), matrix_rows)
                    ],
                )
            ],
        })

    sections.append({
        "title": "Run / Error Log",
        "run_log": run_log,
        "summary": run_log_summary,
        "items": [],
    })

    return {
        "sections": sections,
        "run_log": run_log,
        "run_log_summary": run_log_summary,
        "key_assumptions": {
            "Growth Rates": assumptions.get("revenue_growth_rates", []),
            "Perpetual Growth": _fmt_pct(assumptions.get("perpetual_growth_rate")),
            "Tax Rate": _fmt_pct(assumptions.get("tax_rate")),
            "Risk-Free Rate": _fmt_pct(assumptions.get("risk_free_rate")),
            "Market Risk Premium": _fmt_pct(assumptions.get("market_risk_premium")),
        },
        "final_verdict": {
            "intrinsic_value": _fmt_price(results.get("intrinsic_value_per_share")),
            "market_price": _fmt_price(company.get("current_stock_price")),
            "upside": f"{results.get('upside_pct', 0):.1f}%" if results.get("upside_pct") is not None else "N/A",
            "recommendation": (
                "BUY" if results.get("upside_pct", 0) > 15
                else ("HOLD" if results.get("upside_pct", 0) > -10 else "SELL")
            ),
        },
    }
