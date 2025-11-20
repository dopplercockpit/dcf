#!/usr/bin/env python3
"""
Universal Discounted Cash Flow (DCF) Model
Interactive web-based DCF calculator for any company
With flexible data input interface
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Alpha Vantage API Configuration
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")


def _call_alpha_vantage(params: dict):
    """Low-level Alpha Vantage call with basic error handling."""
    if not ALPHAVANTAGE_API_KEY:
        raise RuntimeError(
            "ALPHAVANTAGE_API_KEY environment variable is not set."
        )

    query = dict(params)
    query["apikey"] = ALPHAVANTAGE_API_KEY

    resp = requests.get(ALPHAVANTAGE_BASE_URL, params=query, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Alpha Vantage uses 'Note' and 'Error Message' for issues
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage rate limit / note: {data['Note']}")
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")

    return data


def fetch_company_and_cashflows(ticker: str):
    """Fetch company snapshot + last 12 quarters of CF data from Alpha Vantage."""
    ticker = ticker.upper().strip()

    # 1) Company overview (fundamentals: name, shares, debt, cash, beta, etc.)
    overview = _call_alpha_vantage({
        "function": "OVERVIEW",
        "symbol": ticker
    })

    # 2) Real-time / latest quote for current price
    quote = _call_alpha_vantage({
        "function": "GLOBAL_QUOTE",
        "symbol": ticker
    })

    # 3) Cash flow statement (quarterly)
    cash_flow = _call_alpha_vantage({
        "function": "CASH_FLOW",
        "symbol": ticker
    })

    # ---- company_data for your model ----
    # Alpha Vantage fundamentals are in absolute USD; your UI expects millions
    def _to_millions(value):
        try:
            return float(value) / 1_000_000
        except (TypeError, ValueError):
            return 0.0

    try:
        price_str = quote["Global Quote"]["05. price"]
        current_price = float(price_str)
    except Exception:
        current_price = 0.0

    company_data = {
        "ticker": ticker,
        "company_name": overview.get("Name", ticker),
        "current_stock_price": current_price,
        "shares_outstanding": _to_millions(overview.get("SharesOutstanding")),
        "total_debt": _to_millions(overview.get("TotalDebt")),
        "cash": _to_millions(
            overview.get("CashAndCashEquivalentsAtCarryingValue")
        ),
    }

    # ---- historical_data (quarters, ocf, capex, net income) ----
    quarterly_reports = cash_flow.get("quarterlyReports", [])

    # Alpha Vantage returns most recent first → reverse to get chronological
    quarterly_reports = list(quarterly_reports)[:12]
    quarterly_reports.reverse()

    quarters = []
    operating_cf = []
    capex = []
    net_income = []

    for r in quarterly_reports:
        date = r.get("fiscalDateEnding")  # e.g. "2024-09-30"
        quarters.append(date or "N/A")

        operating_cf.append(_to_millions(r.get("operatingCashflow")))
        capex.append(_to_millions(r.get("capitalExpenditures")))
        net_income.append(_to_millions(r.get("netIncome")))

    historical_data = {
        "quarters": quarters,
        "operating_cash_flow": operating_cf,
        "capex": capex,
        "net_income": net_income,
    }

    # Optional: hints for model assumptions (e.g. beta)
    assumptions_hint = {}
    try:
        assumptions_hint["beta"] = float(overview.get("Beta"))
    except (TypeError, ValueError):
        pass

    return company_data, historical_data, assumptions_hint


class DCFModel:
    """Comprehensive DCF Model Calculator"""

    def __init__(self, company_data, historical_data, assumptions):
        self.company = company_data
        self.historical = historical_data
        self.assumptions = assumptions
        self.results = {}

    def calculate_wacc(self):
        """Calculate Weighted Average Cost of Capital (WACC)"""
        # Cost of Equity using CAPM
        cost_of_equity = (self.assumptions['risk_free_rate'] + 
                         self.assumptions['beta'] * self.assumptions['market_risk_premium'])
        
        # Market Cap
        market_cap = self.company['shares_outstanding'] * self.company['current_stock_price']
        
        # Net Debt
        net_debt = self.company['total_debt'] - self.company['cash']
        
        # Enterprise Value
        enterprise_value = market_cap + net_debt
        
        # Weights
        equity_weight = market_cap / enterprise_value if enterprise_value > 0 else 1.0
        debt_weight = net_debt / enterprise_value if enterprise_value > 0 else 0.0
        
        # After-tax cost of debt
        after_tax_cost_debt = self.assumptions['cost_of_debt'] * (1 - self.assumptions['tax_rate'])
        
        # WACC
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_debt)
        
        return {
            'wacc': wacc,
            'cost_of_equity': cost_of_equity,
            'after_tax_cost_debt': after_tax_cost_debt,
            'equity_weight': equity_weight,
            'debt_weight': debt_weight,
            'market_cap': market_cap,
            'net_debt': net_debt,
            'enterprise_value': enterprise_value
        }
    
    def calculate_historical_metrics(self):
        """Calculate historical free cash flow and other metrics"""
        fcf = []
        quarters = self.historical.get('quarters', [])
        ocf = self.historical.get('operating_cash_flow', [])
        capex = self.historical.get('capex', [])
        
        for i in range(len(ocf)):
            fcf.append(ocf[i] + capex[i])  # capex is negative
        
        # TTM (last 4 quarters)
        ttm_length = min(4, len(fcf))
        ttm_fcf = sum(fcf[-ttm_length:]) if fcf else 0
        avg_fcf = ttm_fcf / ttm_length if ttm_length > 0 else 0
        
        ttm_operating_cf = sum(ocf[-ttm_length:]) if ocf else 0
        ttm_capex = sum(capex[-ttm_length:]) if capex else 0
        
        net_income = self.historical.get('net_income', [])
        ttm_net_income = sum(net_income[-ttm_length:]) if net_income else 0
        
        return {
            'quarterly_fcf': fcf,
            'avg_quarterly_fcf': avg_fcf,
            'ttm_fcf': ttm_fcf,
            'ttm_operating_cf': ttm_operating_cf,
            'ttm_capex': ttm_capex,
            'ttm_net_income': ttm_net_income
        }
    
    def project_cash_flows(self, base_fcf):
        """Project future free cash flows"""
        projected_fcf = []
        growth_rates = self.assumptions['revenue_growth_rates']
        
        for year in range(self.assumptions['forecast_years']):
            if year < len(growth_rates):
                growth = growth_rates[year]
            else:
                growth = growth_rates[-1] if growth_rates else 0.03
            
            if year == 0:
                fcf = base_fcf * (1 + growth)
            else:
                fcf = projected_fcf[-1] * (1 + growth)
            
            projected_fcf.append(fcf)
        
        return projected_fcf
    
    def calculate_terminal_value(self, final_fcf, wacc):
        """Calculate terminal value using perpetual growth method"""
        g = self.assumptions['perpetual_growth_rate']
        
        # Ensure WACC > growth rate
        if wacc <= g:
            g = wacc * 0.5  # Adjust growth rate to be safe
        
        terminal_value = (final_fcf * (1 + g)) / (wacc - g)
        return terminal_value
    
    def calculate_dcf_valuation(self):
        """Perform complete DCF valuation"""
        # Calculate WACC
        wacc_results = self.calculate_wacc()
        wacc = wacc_results['wacc']
        
        # Historical metrics
        hist_metrics = self.calculate_historical_metrics()
        base_fcf = hist_metrics['ttm_fcf']
        
        # Project cash flows
        projected_fcf = self.project_cash_flows(base_fcf)
        
        # Calculate present value of projected cash flows
        pv_fcf = []
        for year, fcf in enumerate(projected_fcf, 1):
            pv = fcf / ((1 + wacc) ** year)
            pv_fcf.append(pv)
        
        # Terminal value
        if projected_fcf:
            terminal_value = self.calculate_terminal_value(projected_fcf[-1], wacc)
            pv_terminal_value = terminal_value / ((1 + wacc) ** len(projected_fcf))
        else:
            terminal_value = 0
            pv_terminal_value = 0
        
        # Enterprise value
        enterprise_value_dcf = sum(pv_fcf) + pv_terminal_value
        
        # Equity value
        equity_value = enterprise_value_dcf - self.company['total_debt'] + self.company['cash']
        
        # Per share value
        intrinsic_value_per_share = equity_value / self.company['shares_outstanding'] if self.company['shares_outstanding'] > 0 else 0
        
        # Current market value
        current_market_value = self.company['current_stock_price']
        
        # Upside/Downside
        if current_market_value > 0:
            upside_pct = ((intrinsic_value_per_share - current_market_value) / current_market_value) * 100
        else:
            upside_pct = 0
        
        # IRR Calculation (simplified)
        irr = self.calculate_irr(projected_fcf, terminal_value, wacc_results['enterprise_value'])
        
        # EV Multiples
        ev_fcf_multiple = wacc_results['enterprise_value'] / hist_metrics['ttm_fcf'] if hist_metrics['ttm_fcf'] > 0 else 0
        
        results = {
            'wacc_results': wacc_results,
            'historical_metrics': hist_metrics,
            'projected_fcf': projected_fcf,
            'pv_fcf': pv_fcf,
            'terminal_value': terminal_value,
            'pv_terminal_value': pv_terminal_value,
            'enterprise_value_dcf': enterprise_value_dcf,
            'equity_value': equity_value,
            'intrinsic_value_per_share': intrinsic_value_per_share,
            'current_market_value': current_market_value,
            'upside_pct': upside_pct,
            'irr': irr,
            'ev_fcf_multiple': ev_fcf_multiple,
        }
        
        self.results = results
        return results
    
    def calculate_irr(self, cash_flows, terminal_value, initial_investment):
        """Calculate Internal Rate of Return (simplified)"""
        if not cash_flows or initial_investment <= 0:
            return 0
        
        total_future_value = sum(cash_flows) + terminal_value
        years = len(cash_flows)
        
        try:
            irr = (total_future_value / initial_investment) ** (1 / years) - 1
        except:
            irr = 0
        
        return irr

@app.route('/')
def index():
    """Render main page"""
    return render_template('index_input.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """API endpoint to calculate DCF"""
    try:
        data = request.json
        
        company_data = data.get('company_data', {})
        historical_data = data.get('historical_data', {})
        assumptions = data.get('assumptions', {})
        
        # Validate required fields
        required_company = ['ticker', 'company_name', 'shares_outstanding', 'current_stock_price', 'total_debt', 'cash']
        required_historical = ['quarters', 'operating_cash_flow', 'capex']
        required_assumptions = ['tax_rate', 'risk_free_rate', 'market_risk_premium', 'beta', 
                               'cost_of_debt', 'perpetual_growth_rate', 'revenue_growth_rates', 'forecast_years']
        
        for field in required_company:
            if field not in company_data:
                return jsonify({'success': False, 'error': f'Missing company field: {field}'}), 400
        
        for field in required_historical:
            if field not in historical_data:
                return jsonify({'success': False, 'error': f'Missing historical field: {field}'}), 400
        
        for field in required_assumptions:
            if field not in assumptions:
                return jsonify({'success': False, 'error': f'Missing assumption field: {field}'}), 400
        
        # Create model and calculate
        model = DCFModel(company_data, historical_data, assumptions)
        results = model.calculate_dcf_valuation()
        
        # Add company data and historical data
        results['company_data'] = company_data
        results['historical_data'] = historical_data
        results['assumptions'] = assumptions
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/alpha_vantage', methods=['GET'])
def alpha_vantage_lookup():
    """Fetch company + historical data from Alpha Vantage for a given ticker."""
    ticker = request.args.get('ticker', '').strip()
    if not ticker:
        return jsonify({
            "success": False,
            "error": "Ticker parameter is required (?ticker=H)"
        }), 400

    try:
        company_data, historical_data, assumptions_hint = \
            fetch_company_and_cashflows(ticker)

        return jsonify({
            "success": True,
            "company_data": company_data,
            "historical_data": historical_data,
            "assumptions_hint": assumptions_hint
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route('/api/defaults')
def get_defaults():
    """Get default values"""
    defaults = {
        'assumptions': {
            'tax_rate': 0.21,
            'risk_free_rate': 0.045,
            'market_risk_premium': 0.08,
            'beta': 1.15,
            'cost_of_debt': 0.05,
            'perpetual_growth_rate': 0.025,
            'revenue_growth_rates': [0.06, 0.055, 0.05, 0.045, 0.04],
            'forecast_years': 5
        }
    }
    return jsonify(defaults)


@app.route('/api/analyze', methods=['POST'])
def analyze_ticker():
    """
    Simplified endpoint: Takes ticker + optional assumptions,
    fetches from Alpha Vantage, and runs full DCF calculation.
    """
    try:
        # Check if API key is set
        if not ALPHAVANTAGE_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Alpha Vantage API key is not configured. Please set the ALPHAVANTAGE_API_KEY environment variable.'
            }), 500

        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request: No JSON data received'
            }), 400

        ticker = data.get('ticker', '').strip().upper()

        if not ticker:
            return jsonify({
                'success': False,
                'error': 'Ticker symbol is required'
            }), 400

        print(f"Fetching data for ticker: {ticker}")

        # Fetch data from Alpha Vantage
        try:
            company_data, historical_data, assumptions_hint = \
                fetch_company_and_cashflows(ticker)
            print(f"Successfully fetched data for {ticker}")
        except RuntimeError as e:
            error_msg = str(e)
            print(f"RuntimeError fetching data: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        except Exception as e:
            error_msg = f'Failed to fetch data for {ticker}: {str(e)}'
            print(f"Exception fetching data: {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Get default assumptions
        default_assumptions = {
            'tax_rate': 0.21,
            'risk_free_rate': 0.045,
            'market_risk_premium': 0.08,
            'beta': assumptions_hint.get('beta', 1.15),  # Use fetched beta if available
            'cost_of_debt': 0.05,
            'perpetual_growth_rate': 0.025,
            'revenue_growth_rates': [0.06, 0.055, 0.05, 0.045, 0.04],
            'forecast_years': 5
        }

        # Allow user to override assumptions
        user_assumptions = data.get('assumptions', {})
        assumptions = {**default_assumptions, **user_assumptions}

        print(f"Running DCF calculation for {ticker}")

        # Create model and calculate
        try:
            model = DCFModel(company_data, historical_data, assumptions)
            results = model.calculate_dcf_valuation()
        except Exception as e:
            error_msg = f'Error calculating DCF: {str(e)}'
            print(f"Exception in DCF calculation: {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

        # Add company data and historical data to results
        results['company_data'] = company_data
        results['historical_data'] = historical_data
        results['assumptions'] = assumptions

        print(f"Successfully completed analysis for {ticker}")

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        print(f"Unexpected exception: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Universal DCF Valuation Model")
    print("=" * 60)
    print("\nStarting web server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)