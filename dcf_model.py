#!/usr/bin/env python3
"""
Enhanced Universal DCF Model with Multi-Source Data and Qualitative Analysis
FIXED: Now properly fetches Balance Sheet data and validates data quality
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import re
from collections import Counter
import yfinance as yf

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Configuration
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# --- DATA QUALITY CHECKER ---
class DataQualityChecker:
    """
    Validates financial data quality and flags issues.
    Like a health inspector for your financial data!
    """
    
    @staticmethod
    def check_company_data(company_data):
        """Check if company data has critical fields"""
        issues = []
        warnings = []
        
        # Critical checks (would break DCF)
        if company_data.get('shares_outstanding', 0) <= 0:
            issues.append("❌ Missing shares outstanding - cannot calculate per-share value")
        
        if company_data.get('current_stock_price', 0) <= 0:
            issues.append("❌ Missing current stock price - cannot determine market value")
        
        # Important checks (affects accuracy)
        if company_data.get('total_debt', 0) == 0 and company_data.get('cash', 0) == 0:
            warnings.append("⚠️ Both debt and cash are zero - check if balance sheet data loaded")
        
        if company_data.get('cash', 0) < 0:
            warnings.append("⚠️ Negative cash balance detected - data may be incorrect")
        
        if company_data.get('total_debt', 0) < 0:
            warnings.append("⚠️ Negative debt detected - data may be incorrect")
        
        return issues, warnings
    
    @staticmethod
    def check_historical_data(historical_data):
        """Check if historical cash flow data is complete"""
        issues = []
        warnings = []
        
        quarters = historical_data.get('quarters', [])
        ocf = historical_data.get('operating_cash_flow', [])
        capex = historical_data.get('capex', [])
        
        if len(quarters) < 4:
            issues.append(f"❌ Only {len(quarters)} quarters of data (need at least 4 for TTM)")
        
        if len(ocf) == 0:
            issues.append("❌ No operating cash flow data")
        
        if len(capex) == 0:
            warnings.append("⚠️ No CapEx data - FCF calculation will be incomplete")
        
        # Check for all-zero data
        if all(x == 0 for x in ocf):
            issues.append("❌ All operating cash flow values are zero")
        
        if all(x == 0 for x in capex):
            warnings.append("⚠️ All CapEx values are zero - unusual for most companies")
        
        return issues, warnings
    
    @staticmethod
    def get_data_quality_report(company_data, historical_data):
        """Generate comprehensive data quality report"""
        company_issues, company_warnings = DataQualityChecker.check_company_data(company_data)
        hist_issues, hist_warnings = DataQualityChecker.check_historical_data(historical_data)
        
        all_issues = company_issues + hist_issues
        all_warnings = company_warnings + hist_warnings
        
        # Determine overall quality
        if len(all_issues) > 0:
            quality = "POOR"
            quality_emoji = "🔴"
        elif len(all_warnings) > 2:
            quality = "FAIR"
            quality_emoji = "🟡"
        elif len(all_warnings) > 0:
            quality = "GOOD"
            quality_emoji = "🟢"
        else:
            quality = "EXCELLENT"
            quality_emoji = "✅"
        
        return {
            'quality': quality,
            'quality_emoji': quality_emoji,
            'issues': all_issues,
            'warnings': all_warnings,
            'usable': len(all_issues) == 0
        }


# --- REDDIT SCRAPER (No Authentication Required!) ---
class RedditScraper:
    """
    Scrapes Reddit without authentication using the public JSON API.
    """
    
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'DCF-Model-Educational-Tool/1.0'
        }
    
    def search_ticker_mentions(self, ticker, limit=50):
        """Search multiple finance subreddits for ticker mentions."""
        subreddits = ['stocks', 'investing', 'wallstreetbets', 'StockMarket', 'valueinvesting']
        all_posts = []
        
        for subreddit in subreddits:
            try:
                url = f"{self.BASE_URL}/r/{subreddit}/search.json"
                params = {
                    'q': ticker,
                    'limit': limit // len(subreddits),
                    'restrict_sr': 'true',
                    'sort': 'relevance',
                    't': 'month'
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        all_posts.append({
                            'title': post_data.get('title', ''),
                            'text': post_data.get('selftext', ''),
                            'score': post_data.get('score', 0),
                            'num_comments': post_data.get('num_comments', 0),
                            'created': post_data.get('created_utc', 0),
                            'url': f"{self.BASE_URL}{post_data.get('permalink', '')}",
                            'subreddit': subreddit
                        })
                        
            except Exception as e:
                print(f"Error scraping r/{subreddit}: {e}")
                continue
        
        return all_posts
    
    def analyze_sentiment(self, posts, ticker):
        """Analyze sentiment from Reddit posts using keyword analysis."""
        
        positive_words = [
            'buy', 'bullish', 'moon', 'rocket', 'gains', 'calls', 'long',
            'undervalued', 'opportunity', 'growth', 'breakout', 'strong',
            'upgrade', 'beat', 'positive', 'profit', 'revenue', 'innovation'
        ]
        
        negative_words = [
            'sell', 'bearish', 'puts', 'short', 'overvalued', 'dump',
            'crash', 'red', 'losses', 'weak', 'downgrade', 'miss',
            'negative', 'debt', 'lawsuit', 'recall', 'bankruptcy'
        ]
        
        sentiment_scores = []
        keyword_frequency = Counter()
        post_highlights = []
        
        for post in posts:
            text = (post['title'] + ' ' + post['text']).lower()
            
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)
            
            weight = 1 + (post['score'] / 100)
            
            if pos_count > 0 or neg_count > 0:
                score = ((pos_count - neg_count) / (pos_count + neg_count)) * weight
                sentiment_scores.append(score)
                
                for word in positive_words:
                    if word in text:
                        keyword_frequency[f"📈 {word}"] += 1
                for word in negative_words:
                    if word in text:
                        keyword_frequency[f"📉 {word}"] += 1
                
                if post['score'] > 50 or abs(score) > 0.5:
                    post_highlights.append({
                        'title': post['title'][:100],
                        'score': post['score'],
                        'sentiment': 'Bullish' if score > 0 else 'Bearish',
                        'url': post['url'],
                        'subreddit': post['subreddit']
                    })
        
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            sentiment_percentage = (avg_sentiment + 1) / 2 * 100
        else:
            avg_sentiment = 0
            sentiment_percentage = 50
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_percentage': sentiment_percentage,
            'total_posts': len(posts),
            'analyzed_posts': len(sentiment_scores),
            'keyword_frequency': dict(keyword_frequency.most_common(10)),
            'post_highlights': sorted(post_highlights, 
                                    key=lambda x: x['score'], 
                                    reverse=True)[:5]
        }


# --- NEWS API INTEGRATION ---
class NewsAnalyzer:
    """Fetches and analyzes recent news about a company."""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_company_news(self, company_name, ticker, days=30):
        """Fetch recent news articles about the company."""
        if not self.api_key:
            return []
        
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            params = {
                'q': f'"{company_name}" OR {ticker}',
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'pageSize': 50
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                return [{
                    'title': article['title'],
                    'description': article.get('description', ''),
                    'url': article['url'],
                    'source': article['source']['name'],
                    'published_at': article['publishedAt'],
                    'content': article.get('content', '')
                } for article in articles]
            
        except Exception as e:
            print(f"Error fetching news: {e}")
        
        return []
    
    def analyze_news_sentiment(self, articles):
        """Analyze news sentiment."""
        
        negative_keywords = [
            'lawsuit', 'investigation', 'decline', 'loss', 'scandal',
            'controversy', 'warning', 'risk', 'concern', 'pressure',
            'layoff', 'restructure', 'bankruptcy', 'fraud', 'recall',
            'downgrade', 'disappointing', 'weak', 'struggle', 'plunge'
        ]
        
        positive_keywords = [
            'growth', 'profit', 'innovation', 'expansion', 'partnership',
            'acquisition', 'upgrade', 'breakthrough', 'record', 'strong',
            'success', 'launch', 'beat', 'exceed', 'outperform',
            'revenue', 'margin', 'efficient', 'strategic', 'leading'
        ]
        
        sentiment_scores = []
        risk_flags = []
        opportunity_flags = []
        
        for article in articles:
            text = (article['title'] + ' ' + article.get('description', '')).lower()
            
            pos_count = sum(1 for word in positive_keywords if word in text)
            neg_count = sum(1 for word in negative_keywords if word in text)
            
            if pos_count > 0 or neg_count > 0:
                score = (pos_count - neg_count) / (pos_count + neg_count)
                sentiment_scores.append(score)
                
                if neg_count >= 2:
                    risk_flags.append({
                        'title': article['title'][:100],
                        'source': article['source'],
                        'url': article['url'],
                        'date': article['published_at']
                    })
                
                if pos_count >= 2:
                    opportunity_flags.append({
                        'title': article['title'][:100],
                        'source': article['source'],
                        'url': article['url'],
                        'date': article['published_at']
                    })
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        sentiment_percentage = (avg_sentiment + 1) / 2 * 100
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_percentage': sentiment_percentage,
            'total_articles': len(articles),
            'analyzed_articles': len(sentiment_scores),
            'risk_flags': risk_flags[:5],
            'opportunity_flags': opportunity_flags[:5]
        }


# --- ALPHA VANTAGE FETCHER (FIXED!) ---
def _call_alpha_vantage(params: dict):
    """Low-level Alpha Vantage call with basic error handling."""
    if not ALPHAVANTAGE_API_KEY:
        raise RuntimeError("ALPHAVANTAGE_API_KEY environment variable is not set.")
    
    query = dict(params)
    query["apikey"] = ALPHAVANTAGE_API_KEY
    
    resp = requests.get("https://www.alphavantage.co/query", params=query, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage rate limit / note: {data['Note']}")
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
    
    return data


def fetch_from_yahoo(ticker: str):
    """
    Fallback: Fetch company data from Yahoo Finance using yfinance.
    """
    ticker = ticker.upper().strip()
    print(f"  📊 Fetching data from Yahoo Finance...")

    stock = yf.Ticker(ticker)
    info = stock.info

    def _to_millions(value):
        """Convert absolute USD to millions"""
        try:
            if value is None:
                return 0.0
            return float(value) / 1_000_000
        except (TypeError, ValueError):
            return 0.0

    # Get current price
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0.0

    # Company data from info
    company_data = {
        "ticker": ticker,
        "company_name": info.get("longName") or info.get("shortName") or ticker,
        "current_stock_price": current_price,
        "shares_outstanding": _to_millions(info.get("sharesOutstanding")),
        "total_debt": _to_millions(info.get("totalDebt")),
        "short_term_debt": _to_millions(info.get("currentDebt", 0)),
        "long_term_debt": _to_millions(info.get("longTermDebt", 0)),
        "cash": _to_millions(info.get("totalCash")),
        "total_assets": _to_millions(info.get("totalAssets", 0)),
        "total_liabilities": _to_millions(info.get("totalDebt", 0)),  # Approximation
        "shareholders_equity": _to_millions(info.get("bookValue", 0) * info.get("sharesOutstanding", 0)),
    }

    # Get quarterly cash flow data
    try:
        cf = stock.quarterly_cashflow
        if cf is not None and not cf.empty:
            # Get up to 12 quarters
            cf = cf.iloc[:, :12]

            quarters = []
            operating_cf = []
            capex = []
            net_income = []

            for col in cf.columns:
                quarters.append(col.strftime('%Y-%m-%d'))

                # Operating cash flow
                ocf = 0.0
                for key in ['Operating Cash Flow', 'Total Cash From Operating Activities']:
                    if key in cf.index:
                        ocf = _to_millions(cf.loc[key, col])
                        break
                operating_cf.append(ocf)

                # CapEx
                capex_val = 0.0
                for key in ['Capital Expenditure', 'Capital Expenditures']:
                    if key in cf.index:
                        capex_val = abs(_to_millions(cf.loc[key, col]))
                        break
                capex.append(capex_val)

                # Net income
                ni = 0.0
                if 'Net Income' in cf.index:
                    ni = _to_millions(cf.loc['Net Income', col])
                net_income.append(ni)

            # Reverse to chronological order
            quarters.reverse()
            operating_cf.reverse()
            capex.reverse()
            net_income.reverse()
        else:
            quarters = []
            operating_cf = []
            capex = []
            net_income = []
    except Exception as e:
        print(f"  ⚠️ Could not fetch cash flow data: {e}")
        quarters = []
        operating_cf = []
        capex = []
        net_income = []

    historical_data = {
        "quarters": quarters,
        "operating_cash_flow": operating_cf,
        "capex": capex,
        "net_income": net_income,
    }

    assumptions_hint = {}
    beta = info.get("beta")
    if beta:
        assumptions_hint["beta"] = float(beta)

    raw_financials = {
        "balance_sheet_date": "Yahoo Finance",
        "raw_data": {},
        "source": "Yahoo Finance (yfinance)"
    }

    return company_data, historical_data, assumptions_hint, raw_financials


def fetch_company_and_cashflows(ticker: str):
    """
    Fetch company snapshot + cash flows + BALANCE SHEET data.
    Tries Alpha Vantage first, falls back to Yahoo Finance.
    """
    ticker = ticker.upper().strip()

    # Try Alpha Vantage first
    if ALPHAVANTAGE_API_KEY:
        try:
            import time

            print(f"  📊 Fetching OVERVIEW...")
            overview = _call_alpha_vantage({
                "function": "OVERVIEW",
                "symbol": ticker
            })
            time.sleep(1)  # Delay to avoid rate limiting

            print(f"  💰 Fetching QUOTE...")
            quote = _call_alpha_vantage({
                "function": "GLOBAL_QUOTE",
                "symbol": ticker
            })
            time.sleep(1)

            print(f"  💸 Fetching CASH_FLOW...")
            cash_flow = _call_alpha_vantage({
                "function": "CASH_FLOW",
                "symbol": ticker
            })
            time.sleep(1)

            # THE FIX: Fetch balance sheet for accurate Cash and Debt!
            print(f"  🏦 Fetching BALANCE_SHEET...")
            balance_sheet = _call_alpha_vantage({
                "function": "BALANCE_SHEET",
                "symbol": ticker
            })
            time.sleep(1)

            # Also fetch income statement for additional validation
            print(f"  📈 Fetching INCOME_STATEMENT...")
            income_statement = _call_alpha_vantage({
                "function": "INCOME_STATEMENT",
                "symbol": ticker
            })
        except Exception as e:
            print(f"  ⚠️ Alpha Vantage failed: {e}")
            print(f"  🔄 Falling back to Yahoo Finance...")
            return fetch_from_yahoo(ticker)
    else:
        print(f"  ℹ️ No Alpha Vantage API key, using Yahoo Finance...")
        return fetch_from_yahoo(ticker)
    
    def _to_millions(value):
        """Convert absolute USD to millions"""
        try:
            if value is None or value == 'None' or value == '':
                return 0.0
            return float(value) / 1_000_000
        except (TypeError, ValueError):
            return 0.0
    
    # Get current price
    try:
        price_str = quote["Global Quote"]["05. price"]
        current_price = float(price_str)
    except Exception:
        current_price = 0.0
    
    # Extract Cash and Debt from BALANCE SHEET (most recent quarter)
    bs_reports = balance_sheet.get("quarterlyReports", [])
    latest_bs = bs_reports[0] if bs_reports else {}
    
    # Try multiple field names for Total Debt
    raw_debt = (
        latest_bs.get("shortLongTermDebtTotal") or 
        latest_bs.get("totalDebt") or 
        latest_bs.get("longTermDebt") or 
        "0"
    )
    
    # Try multiple field names for Cash
    raw_cash = (
        latest_bs.get("cashAndCashEquivalentsAtCarryingValue") or 
        latest_bs.get("cashAndShortTermInvestments") or 
        latest_bs.get("cash") or
        "0"
    )
    
    # Also get short-term debt if available
    short_term_debt = _to_millions(latest_bs.get("shortTermDebt", "0"))
    long_term_debt = _to_millions(latest_bs.get("longTermDebt", "0"))
    
    # Calculate total debt (short-term + long-term)
    total_debt = _to_millions(raw_debt)
    if total_debt == 0 and (short_term_debt > 0 or long_term_debt > 0):
        total_debt = short_term_debt + long_term_debt
    
    company_data = {
        "ticker": ticker,
        "company_name": overview.get("Name", ticker),
        "current_stock_price": current_price,
        "shares_outstanding": _to_millions(overview.get("SharesOutstanding")),
        "total_debt": total_debt,
        "short_term_debt": short_term_debt,
        "long_term_debt": long_term_debt,
        "cash": _to_millions(raw_cash),
        "total_assets": _to_millions(latest_bs.get("totalAssets", "0")),
        "total_liabilities": _to_millions(latest_bs.get("totalLiabilities", "0")),
        "shareholders_equity": _to_millions(latest_bs.get("totalShareholderEquity", "0")),
    }
    
    # Historical cash flow data
    quarterly_reports = cash_flow.get("quarterlyReports", [])
    quarterly_reports = list(quarterly_reports)[:12]
    quarterly_reports.reverse()
    
    quarters = []
    operating_cf = []
    capex = []
    net_income = []
    
    for r in quarterly_reports:
        date = r.get("fiscalDateEnding")
        quarters.append(date or "N/A")
        
        operating_cf.append(_to_millions(r.get("operatingCashflow")))
        capex.append(_to_millions(r.get("capitalExpenditures")))
        
        # Get net income from cash flow statement
        ni = _to_millions(r.get("netIncome", "0"))
        net_income.append(ni)
    
    # If net income is all zeros, try to get from income statement
    if all(x == 0 for x in net_income):
        is_reports = income_statement.get("quarterlyReports", [])
        is_reports = list(is_reports)[:12]
        is_reports.reverse()
        net_income = [_to_millions(r.get("netIncome", "0")) for r in is_reports]
    
    historical_data = {
        "quarters": quarters,
        "operating_cash_flow": operating_cf,
        "capex": capex,
        "net_income": net_income,
    }
    
    assumptions_hint = {}
    try:
        assumptions_hint["beta"] = float(overview.get("Beta"))
    except (TypeError, ValueError):
        pass
    
    # Add raw financial statement data for debugging/display
    raw_financials = {
        "balance_sheet_date": latest_bs.get("fiscalDateEnding", "N/A"),
        "raw_data": {
            "cash_from_bs": raw_cash,
            "debt_from_bs": raw_debt,
            "short_term_debt": latest_bs.get("shortTermDebt", "0"),
            "long_term_debt": latest_bs.get("longTermDebt", "0"),
            "total_assets": latest_bs.get("totalAssets", "0"),
            "total_liabilities": latest_bs.get("totalLiabilities", "0"),
        }
    }
    
    return company_data, historical_data, assumptions_hint, raw_financials


class DCFModel:
    """Comprehensive DCF Model Calculator with Enhanced Transparency"""
    
    def __init__(self, company_data, historical_data, assumptions):
        self.company = company_data
        self.historical = historical_data
        self.assumptions = assumptions
        self.results = {}
        self.calculation_details = {}
    
    def calculate_wacc(self):
        """Calculate Weighted Average Cost of Capital (WACC)"""
        
        rf = self.assumptions['risk_free_rate']
        beta = self.assumptions['beta']
        mrp = self.assumptions['market_risk_premium']
        
        cost_of_equity = rf + (beta * mrp)
        
        shares = self.company['shares_outstanding']
        price = self.company['current_stock_price']
        market_cap = shares * price
        
        net_debt = self.company['total_debt'] - self.company['cash']
        enterprise_value = market_cap + net_debt
        
        equity_weight = market_cap / enterprise_value if enterprise_value > 0 else 1.0
        debt_weight = net_debt / enterprise_value if enterprise_value > 0 else 0.0
        
        cost_of_debt = self.assumptions['cost_of_debt']
        tax_rate = self.assumptions['tax_rate']
        after_tax_cost_debt = cost_of_debt * (1 - tax_rate)
        
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_debt)
        
        self.calculation_details['wacc'] = {
            'formula': 'WACC = (E/V × Re) + (D/V × Rd × (1-T))',
            'components': {
                'risk_free_rate': rf,
                'beta': beta,
                'market_risk_premium': mrp,
                'cost_of_equity': cost_of_equity,
                'cost_of_debt': cost_of_debt,
                'tax_rate': tax_rate,
                'after_tax_cost_debt': after_tax_cost_debt,
                'market_cap': market_cap,
                'total_debt': self.company['total_debt'],
                'cash': self.company['cash'],
                'net_debt': net_debt,
                'enterprise_value': enterprise_value,
                'equity_weight': equity_weight,
                'debt_weight': debt_weight
            },
            'explanation': 'WACC represents the average rate the company must pay to finance its assets.'
        }
        
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
        """Calculate historical free cash flow and other metrics."""
        fcf = []
        quarters = self.historical.get('quarters', [])
        ocf = self.historical.get('operating_cash_flow', [])
        capex = self.historical.get('capex', [])
        
        for i in range(len(ocf)):
            fcf.append(ocf[i] + capex[i])
        
        ttm_length = min(4, len(fcf))
        ttm_fcf = sum(fcf[-ttm_length:]) if fcf else 0
        avg_fcf = ttm_fcf / ttm_length if ttm_length > 0 else 0
        
        ttm_operating_cf = sum(ocf[-ttm_length:]) if ocf else 0
        ttm_capex = sum(capex[-ttm_length:]) if capex else 0
        
        net_income = self.historical.get('net_income', [])
        ttm_net_income = sum(net_income[-ttm_length:]) if net_income else 0
        
        self.calculation_details['fcf'] = {
            'formula': 'FCF = Operating Cash Flow - Capital Expenditures',
            'components': {
                'ttm_operating_cf': ttm_operating_cf,
                'ttm_capex': ttm_capex,
                'ttm_fcf': ttm_fcf
            },
            'explanation': 'Free Cash Flow represents the cash available after maintaining/expanding the asset base.'
        }
        
        return {
            'quarterly_fcf': fcf,
            'avg_quarterly_fcf': avg_fcf,
            'ttm_fcf': ttm_fcf,
            'ttm_operating_cf': ttm_operating_cf,
            'ttm_capex': ttm_capex,
            'ttm_net_income': ttm_net_income
        }
    
    def project_cash_flows(self, base_fcf):
        """Project future free cash flows."""
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
        """Calculate terminal value using perpetual growth method."""
        g = self.assumptions['perpetual_growth_rate']
        
        if wacc <= g:
            g = wacc * 0.5
        
        terminal_value = (final_fcf * (1 + g)) / (wacc - g)
        
        self.calculation_details['terminal_value'] = {
            'formula': 'TV = FCF(final) × (1 + g) / (WACC - g)',
            'components': {
                'final_fcf': final_fcf,
                'growth_rate': g,
                'wacc': wacc,
                'terminal_value': terminal_value
            },
            'explanation': 'Terminal Value captures the value of all cash flows beyond the forecast period.'
        }
        
        return terminal_value
    
    def calculate_dcf_valuation(self):
        """Perform complete DCF valuation."""
        
        wacc_results = self.calculate_wacc()
        wacc = wacc_results['wacc']
        
        hist_metrics = self.calculate_historical_metrics()
        base_fcf = hist_metrics['ttm_fcf']
        
        projected_fcf = self.project_cash_flows(base_fcf)
        
        pv_fcf = []
        for year, fcf in enumerate(projected_fcf, 1):
            pv = fcf / ((1 + wacc) ** year)
            pv_fcf.append(pv)
        
        if projected_fcf:
            terminal_value = self.calculate_terminal_value(projected_fcf[-1], wacc)
            pv_terminal_value = terminal_value / ((1 + wacc) ** len(projected_fcf))
        else:
            terminal_value = 0
            pv_terminal_value = 0
        
        enterprise_value_dcf = sum(pv_fcf) + pv_terminal_value
        equity_value = enterprise_value_dcf - self.company['total_debt'] + self.company['cash']
        
        intrinsic_value_per_share = equity_value / self.company['shares_outstanding'] if self.company['shares_outstanding'] > 0 else 0
        current_market_value = self.company['current_stock_price']
        
        if current_market_value > 0:
            upside_pct = ((intrinsic_value_per_share - current_market_value) / current_market_value) * 100
        else:
            upside_pct = 0
        
        irr = self.calculate_irr(projected_fcf, terminal_value, wacc_results['enterprise_value'])
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
            'calculation_details': self.calculation_details
        }
        
        self.results = results
        return results
    
    def calculate_irr(self, cash_flows, terminal_value, initial_investment):
        """Calculate Internal Rate of Return (simplified)."""
        if not cash_flows or initial_investment <= 0:
            return 0
        
        total_future_value = sum(cash_flows) + terminal_value
        years = len(cash_flows)
        
        try:
            irr = (total_future_value / initial_investment) ** (1 / years) - 1
        except:
            irr = 0
        
        return irr


# --- FLASK ROUTES ---

@app.route('/')
def index():
    """Render main page"""
    return render_template('index_input.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_ticker():
    """
    Comprehensive analysis endpoint with data quality validation
    """
    try:
        if not ALPHAVANTAGE_API_KEY:
            return jsonify({
                'success': False,
                'error': 'Alpha Vantage API key is not configured.'
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
        
        print(f"\n{'='*60}")
        print(f"Starting comprehensive analysis for {ticker}")
        print(f"{'='*60}\n")
        
        # 1. Fetch financial data from Alpha Vantage
        print(f"[1/4] Fetching financial data from Alpha Vantage...")
        try:
            company_data, historical_data, assumptions_hint, raw_financials = fetch_company_and_cashflows(ticker)
            print(f"✓ Financial data fetched successfully")
            print(f"  Cash: ${company_data['cash']:.2f}M")
            print(f"  Debt: ${company_data['total_debt']:.2f}M")
            print(f"  Shares: {company_data['shares_outstanding']:.2f}M")
        except Exception as e:
            error_msg = f'Failed to fetch financial data: {str(e)}'
            print(f"✗ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # CHECK DATA QUALITY
        print(f"\n📋 Checking data quality...")
        quality_report = DataQualityChecker.get_data_quality_report(company_data, historical_data)
        print(f"  Quality: {quality_report['quality_emoji']} {quality_report['quality']}")
        if quality_report['issues']:
            for issue in quality_report['issues']:
                print(f"    {issue}")
        if quality_report['warnings']:
            for warning in quality_report['warnings']:
                print(f"    {warning}")
        
        # 2. Scrape Reddit sentiment
        print(f"\n[2/4] Scraping Reddit for community sentiment...")
        reddit_data = {}
        try:
            scraper = RedditScraper()
            posts = scraper.search_ticker_mentions(ticker, limit=50)
            reddit_data = scraper.analyze_sentiment(posts, ticker)
            print(f"✓ Reddit sentiment analyzed ({reddit_data['analyzed_posts']} posts)")
        except Exception as e:
            print(f"⚠ Reddit scraping failed: {e}")
            reddit_data = {
                'average_sentiment': 0,
                'sentiment_percentage': 50,
                'total_posts': 0,
                'error': str(e)
            }
        
        # 3. Fetch news articles
        print(f"\n[3/4] Fetching recent news articles...")
        news_data = {}
        try:
            if NEWS_API_KEY:
                news_analyzer = NewsAnalyzer(NEWS_API_KEY)
                articles = news_analyzer.fetch_company_news(
                    company_data['company_name'], 
                    ticker
                )
                news_data = news_analyzer.analyze_news_sentiment(articles)
                news_data['articles'] = articles[:10]
                print(f"✓ News analyzed ({news_data['total_articles']} articles)")
            else:
                print(f"⚠ News API key not configured (optional)")
                news_data = {
                    'average_sentiment': 0,
                    'sentiment_percentage': 50,
                    'total_articles': 0,
                    'message': 'News API key not configured'
                }
        except Exception as e:
            print(f"⚠ News fetching failed: {e}")
            news_data = {
                'average_sentiment': 0,
                'sentiment_percentage': 50,
                'total_articles': 0,
                'error': str(e)
            }
        
        # 4. Calculate DCF valuation
        print(f"\n[4/4] Calculating DCF valuation...")
        default_assumptions = {
            'tax_rate': 0.21,
            'risk_free_rate': 0.045,
            'market_risk_premium': 0.08,
            'beta': assumptions_hint.get('beta', 1.15),
            'cost_of_debt': 0.05,
            'perpetual_growth_rate': 0.025,
            'revenue_growth_rates': [0.06, 0.055, 0.05, 0.045, 0.04],
            'forecast_years': 5
        }
        
        user_assumptions = data.get('assumptions', {})
        assumptions = {**default_assumptions, **user_assumptions}
        
        try:
            model = DCFModel(company_data, historical_data, assumptions)
            results = model.calculate_dcf_valuation()
            print(f"✓ DCF calculation completed")
        except Exception as e:
            error_msg = f'Error calculating DCF: {str(e)}'
            print(f"✗ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        
        # Add all data to results
        results['company_data'] = company_data
        results['historical_data'] = historical_data
        results['assumptions'] = assumptions
        results['reddit_sentiment'] = reddit_data
        results['news_analysis'] = news_data
        results['data_quality'] = quality_report
        results['raw_financials'] = raw_financials
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        print(f"Intrinsic Value: ${results['intrinsic_value_per_share']:.2f}")
        print(f"Current Price: ${results['current_market_value']:.2f}")
        print(f"Upside: {results['upside_pct']:.1f}%")
        print(f"Data Quality: {quality_report['quality']}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        print(f"\n✗ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


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


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Enhanced Universal DCF Valuation Model")
    print("   WITH DATA QUALITY VALIDATION")
    print("=" * 60)
    print("\n✨ Features:")
    print("  • Proper Balance Sheet data fetching")
    print("  • Data quality validation & flags")
    print("  • Reddit sentiment analysis")
    print("  • News article integration")
    print("  • Interactive tooltips")
    print("\nStarting web server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)