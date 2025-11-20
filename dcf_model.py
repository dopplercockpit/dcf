#!/usr/bin/env python3
"""
Enhanced Universal DCF Model with Multi-Source Data and Qualitative Analysis
Now with Reddit sentiment, news integration, and comprehensive transparency
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

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Configuration
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")  # Get free key from newsapi.org

# --- REDDIT SCRAPER (No Authentication Required!) ---
# Think of this as eavesdropping on the financial watercooler - 
# we're listening to what retail investors are saying without needing a Reddit account

class RedditScraper:
    """
    Scrapes Reddit without authentication using the public JSON API.
    It's like reading a newspaper that's freely available on the street corner!
    """
    
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'DCF-Model-Educational-Tool/1.0'
        }
    
    def search_ticker_mentions(self, ticker, limit=50):
        """
        Search multiple finance subreddits for ticker mentions.
        We cast a wide net across the financial fishing holes of Reddit.
        """
        subreddits = ['stocks', 'investing', 'wallstreetbets', 'StockMarket', 'valueinvesting']
        all_posts = []
        
        for subreddit in subreddits:
            try:
                # Reddit's JSON API is publicly accessible - just add .json to the URL!
                url = f"{self.BASE_URL}/r/{subreddit}/search.json"
                params = {
                    'q': ticker,
                    'limit': limit // len(subreddits),  # Distribute our quota across subreddits
                    'restrict_sr': 'true',
                    'sort': 'relevance',
                    't': 'month'  # Last month of posts
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
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
        """
        Analyze sentiment from Reddit posts using keyword analysis.
        This is like reading the room - are people excited or worried?
        
        We use a simple but effective approach: count positive vs negative words.
        Think of it as a tug-of-war between bulls and bears!
        """
        
        # Positive indicators (bulls are charging!)
        positive_words = [
            'buy', 'bullish', 'moon', 'rocket', 'gains', 'calls', 'long',
            'undervalued', 'opportunity', 'growth', 'breakout', 'strong',
            'upgrade', 'beat', 'positive', 'profit', 'revenue', 'innovation'
        ]
        
        # Negative indicators (bears are growling!)
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
            
            # Count sentiment words
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)
            
            # Weight by post engagement (more upvotes = more important opinion)
            weight = 1 + (post['score'] / 100)  # Logarithmic-ish scaling
            
            if pos_count > 0 or neg_count > 0:
                # Calculate sentiment score (-1 to 1, like a seesaw)
                score = ((pos_count - neg_count) / (pos_count + neg_count)) * weight
                sentiment_scores.append(score)
                
                # Track which keywords appear most
                for word in positive_words:
                    if word in text:
                        keyword_frequency[f"📈 {word}"] += 1
                for word in negative_words:
                    if word in text:
                        keyword_frequency[f"📉 {word}"] += 1
                
                # Save interesting posts (high engagement or strong sentiment)
                if post['score'] > 50 or abs(score) > 0.5:
                    post_highlights.append({
                        'title': post['title'][:100],
                        'score': post['score'],
                        'sentiment': 'Bullish' if score > 0 else 'Bearish',
                        'url': post['url'],
                        'subreddit': post['subreddit']
                    })
        
        # Calculate overall sentiment
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            # Convert to percentage (0-100 scale is easier to understand)
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
    """
    Fetches and analyzes recent news about a company.
    This is our window into the real world - what's happening beyond the numbers?
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_company_news(self, company_name, ticker, days=30):
        """
        Fetch recent news articles about the company.
        We search for both the company name and ticker to cast a wide net.
        """
        if not self.api_key:
            return []
        
        try:
            # Calculate date range (like setting a time machine)
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
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
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
        """
        Analyze news sentiment - are journalists painting a rosy or gloomy picture?
        This is like reading between the lines of business journalism.
        """
        
        # Keywords that signal trouble (storm clouds gathering!)
        negative_keywords = [
            'lawsuit', 'investigation', 'decline', 'loss', 'scandal',
            'controversy', 'warning', 'risk', 'concern', 'pressure',
            'layoff', 'restructure', 'bankruptcy', 'fraud', 'recall',
            'downgrade', 'disappointing', 'weak', 'struggle', 'plunge'
        ]
        
        # Keywords that signal opportunity (sun breaking through!)
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
                
                # Flag significant news (the stuff that really matters!)
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
            'risk_flags': risk_flags[:5],  # Top 5 risks
            'opportunity_flags': opportunity_flags[:5]  # Top 5 opportunities
        }


# --- ALPHA VANTAGE FETCHER (Your existing code, enhanced) ---
def _call_alpha_vantage(params: dict):
    """Low-level Alpha Vantage call with basic error handling."""
    if not ALPHAVANTAGE_API_KEY:
        raise RuntimeError("ALPHAVANTAGE_API_KEY environment variable is not set.")
    
    query = dict(params)
    query["apikey"] = ALPHAVANTAGE_API_KEY
    
    resp = requests.get("https://www.alphavantage.co/query", params=query, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage rate limit / note: {data['Note']}")
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
    
    return data


def fetch_company_and_cashflows(ticker: str):
    """
    Fetch company snapshot + last 12 quarters of CF data from Alpha Vantage.
    This is our primary data source - think of it as the company's report card.
    """
    ticker = ticker.upper().strip()
    
    # 1) Company overview (the company's vital statistics)
    overview = _call_alpha_vantage({
        "function": "OVERVIEW",
        "symbol": ticker
    })
    
    # 2) Real-time quote (what's it trading for RIGHT NOW?)
    quote = _call_alpha_vantage({
        "function": "GLOBAL_QUOTE",
        "symbol": ticker
    })
    
    # 3) Cash flow statement (the money trail - where's it coming from and going to?)
    cash_flow = _call_alpha_vantage({
        "function": "CASH_FLOW",
        "symbol": ticker
    })
    
    def _to_millions(value):
        """Convert absolute USD to millions (easier to read)"""
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
        "cash": _to_millions(overview.get("CashAndCashEquivalentsAtCarryingValue")),
    }
    
    # Historical data (the company's financial history)
    quarterly_reports = cash_flow.get("quarterlyReports", [])
    quarterly_reports = list(quarterly_reports)[:12]
    quarterly_reports.reverse()  # Chronological order
    
    quarters = []
    operating_cf = []
    capex = []
    net_income = []
    
    for r in quarterly_reports:
        date = r.get("fiscalDateEnding")
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
    
    assumptions_hint = {}
    try:
        assumptions_hint["beta"] = float(overview.get("Beta"))
    except (TypeError, ValueError):
        pass
    
    return company_data, historical_data, assumptions_hint


class DCFModel:
    """
    Comprehensive DCF Model Calculator with Enhanced Transparency
    
    Think of this as a financial X-ray machine - it lets you see through 
    the outer appearance of a stock price to its true internal value.
    """
    
    def __init__(self, company_data, historical_data, assumptions):
        self.company = company_data
        self.historical = historical_data
        self.assumptions = assumptions
        self.results = {}
        
        # Store calculation details for transparency (show your work!)
        self.calculation_details = {}
    
    def calculate_wacc(self):
        """
        Calculate Weighted Average Cost of Capital (WACC)
        
        METAPHOR: WACC is like the interest rate on a blended loan. Imagine you borrowed
        money from two sources: your rich uncle (equity) and a bank (debt). WACC tells you
        what interest rate you're effectively paying when you blend both sources together.
        """
        
        # Cost of Equity using CAPM (Capital Asset Pricing Model)
        # This answers: "What return do shareholders expect for the risk they're taking?"
        rf = self.assumptions['risk_free_rate']
        beta = self.assumptions['beta']
        mrp = self.assumptions['market_risk_premium']
        
        cost_of_equity = rf + (beta * mrp)
        
        # Market Cap (what the market says the company is worth)
        shares = self.company['shares_outstanding']
        price = self.company['current_stock_price']
        market_cap = shares * price
        
        # Net Debt (total debt minus the cash cushion)
        net_debt = self.company['total_debt'] - self.company['cash']
        
        # Enterprise Value (the total value of the business)
        enterprise_value = market_cap + net_debt
        
        # Weights (what percentage of funding comes from each source?)
        equity_weight = market_cap / enterprise_value if enterprise_value > 0 else 1.0
        debt_weight = net_debt / enterprise_value if enterprise_value > 0 else 0.0
        
        # After-tax cost of debt (debt is cheaper because interest is tax-deductible!)
        cost_of_debt = self.assumptions['cost_of_debt']
        tax_rate = self.assumptions['tax_rate']
        after_tax_cost_debt = cost_of_debt * (1 - tax_rate)
        
        # WACC Formula: (Equity% × Equity Cost) + (Debt% × After-tax Debt Cost)
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_debt)
        
        # Store calculation details for tooltips
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
            'explanation': 'WACC represents the average rate the company must pay to finance its assets. It\'s the hurdle rate for investments - projects must earn more than this to create value.'
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
        """
        Calculate historical free cash flow and other metrics.
        
        METAPHOR: Free Cash Flow is like your take-home pay after all the bills are paid.
        It's the money left over that the company can use to pay dividends, buy back stock,
        or invest in growth - the truly "free" money.
        """
        fcf = []
        quarters = self.historical.get('quarters', [])
        ocf = self.historical.get('operating_cash_flow', [])
        capex = self.historical.get('capex', [])
        
        # FCF = Operating Cash Flow + CapEx (CapEx is negative, so we're subtracting it)
        for i in range(len(ocf)):
            fcf.append(ocf[i] + capex[i])
        
        # TTM = Trailing Twelve Months (the last 4 quarters)
        ttm_length = min(4, len(fcf))
        ttm_fcf = sum(fcf[-ttm_length:]) if fcf else 0
        avg_fcf = ttm_fcf / ttm_length if ttm_length > 0 else 0
        
        ttm_operating_cf = sum(ocf[-ttm_length:]) if ocf else 0
        ttm_capex = sum(capex[-ttm_length:]) if capex else 0
        
        net_income = self.historical.get('net_income', [])
        ttm_net_income = sum(net_income[-ttm_length:]) if net_income else 0
        
        # Store calculation details
        self.calculation_details['fcf'] = {
            'formula': 'FCF = Operating Cash Flow - Capital Expenditures',
            'components': {
                'ttm_operating_cf': ttm_operating_cf,
                'ttm_capex': ttm_capex,
                'ttm_fcf': ttm_fcf
            },
            'explanation': 'Free Cash Flow represents the cash available after maintaining/expanding the asset base. It\'s the ultimate measure of financial health.'
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
        """
        Project future free cash flows.
        
        METAPHOR: This is like predicting how much taller a child will grow each year.
        We use growth rates that typically slow down over time (fast growth when young,
        slower growth when mature).
        """
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
        """
        Calculate terminal value using perpetual growth method.
        
        METAPHOR: Terminal value is like valuing a rental property based on the rent it'll
        generate forever. We assume the company keeps growing at a steady, sustainable rate
        into perpetuity (Latin for "forever and ever").
        """
        g = self.assumptions['perpetual_growth_rate']
        
        # Safety check: WACC must be greater than growth rate (otherwise we'd have infinite value!)
        if wacc <= g:
            g = wacc * 0.5
        
        # Gordon Growth Model: TV = FCF × (1 + g) / (WACC - g)
        terminal_value = (final_fcf * (1 + g)) / (wacc - g)
        
        self.calculation_details['terminal_value'] = {
            'formula': 'TV = FCF(final) × (1 + g) / (WACC - g)',
            'components': {
                'final_fcf': final_fcf,
                'growth_rate': g,
                'wacc': wacc,
                'terminal_value': terminal_value
            },
            'explanation': 'Terminal Value captures the value of all cash flows beyond the forecast period. It often represents 70-80% of total value.'
        }
        
        return terminal_value
    
    def calculate_dcf_valuation(self):
        """
        Perform complete DCF valuation.
        
        METAPHOR: DCF valuation is like determining how much you'd pay today for a machine
        that prints money every year. But there's a catch: money in the future is worth less
        than money today (because of inflation and opportunity cost), so we "discount" 
        future cash flows to present value.
        """
        
        # Calculate WACC (our discount rate)
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
            # PV = FV / (1 + r)^n
            pv = fcf / ((1 + wacc) ** year)
            pv_fcf.append(pv)
        
        # Terminal value
        if projected_fcf:
            terminal_value = self.calculate_terminal_value(projected_fcf[-1], wacc)
            pv_terminal_value = terminal_value / ((1 + wacc) ** len(projected_fcf))
        else:
            terminal_value = 0
            pv_terminal_value = 0
        
        # Enterprise value (sum of all present values)
        enterprise_value_dcf = sum(pv_fcf) + pv_terminal_value
        
        # Equity value (enterprise value adjusted for debt and cash)
        equity_value = enterprise_value_dcf - self.company['total_debt'] + self.company['cash']
        
        # Per share value (divide by number of shares)
        intrinsic_value_per_share = equity_value / self.company['shares_outstanding'] if self.company['shares_outstanding'] > 0 else 0
        
        # Current market value
        current_market_value = self.company['current_stock_price']
        
        # Upside/Downside (how much room to run or fall?)
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
            'calculation_details': self.calculation_details  # The "show your work" section!
        }
        
        self.results = results
        return results
    
    def calculate_irr(self, cash_flows, terminal_value, initial_investment):
        """
        Calculate Internal Rate of Return (simplified).
        
        METAPHOR: IRR is like calculating the average annual return on an investment.
        If you buy a stock today and sell it in 5 years, what's your annualized return?
        """
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
    Comprehensive analysis endpoint that fetches:
    1. Financial data from Alpha Vantage
    2. Reddit sentiment
    3. News articles
    4. Calculates DCF with full transparency
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
            company_data, historical_data, assumptions_hint = fetch_company_and_cashflows(ticker)
            print(f"✓ Financial data fetched successfully")
        except Exception as e:
            error_msg = f'Failed to fetch financial data: {str(e)}'
            print(f"✗ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
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
                news_data['articles'] = articles[:10]  # Top 10 articles
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
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        print(f"Intrinsic Value: ${results['intrinsic_value_per_share']:.2f}")
        print(f"Current Price: ${results['current_market_value']:.2f}")
        print(f"Upside: {results['upside_pct']:.1f}%")
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
    print("=" * 60)
    print("\n✨ New Features:")
    print("  • Reddit sentiment analysis")
    print("  • News article integration")
    print("  • Interactive tooltips with full calculations")
    print("  • Educational links to Investopedia")
    print("\nStarting web server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)