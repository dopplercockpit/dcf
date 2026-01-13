# ⚡ Quick-Start Implementation Guide

This file contains ACTUAL CODE you can copy-paste to add critical features.
No theory—just working code with explanations.

---

## 🔧 Implementation 1: Add Health Check Endpoint (5 minutes)

Add this to the **TOP** of `dcf_model.py`, right after your imports:

```python
from datetime import datetime
import sys

# Track app startup time
APP_START_TIME = datetime.utcnow()
REQUEST_COUNTER = {'total': 0, 'errors': 0}
```

Add this **BEFORE** your existing routes (around line 400):

```python
@app.route('/api/health')
def health_check():
    """Health check for monitoring services (Render, UptimeRobot, etc.)"""
    health = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': int((datetime.utcnow() - APP_START_TIME).total_seconds()),
        'checks': {}
    }
    
    # Check API keys
    health['checks']['alpha_vantage'] = {
        'configured': bool(ALPHAVANTAGE_API_KEY),
        'critical': True
    }
    
    # Check database
    try:
        session = get_session()
        session.execute("SELECT 1")
        session.close()
        health['checks']['database'] = {'status': 'healthy', 'critical': True}
    except Exception as e:
        health['checks']['database'] = {'status': 'error', 'message': str(e), 'critical': True}
        health['status'] = 'unhealthy'
        return jsonify(health), 503
    
    return jsonify(health), 200


@app.before_request
def count_requests():
    """Count requests for monitoring"""
    REQUEST_COUNTER['total'] += 1
```

**Test it:**
```bash
python dcf_model.py
# In another terminal:
curl http://localhost:5000/api/health
# Should return: {"status": "healthy", ...}
```

---

## 🔧 Implementation 2: Add API Caching (10 minutes)

Add this **AFTER** your imports in `dcf_model.py`:

```python
from functools import wraps
from datetime import datetime, timedelta
import json

# Simple in-memory cache
_API_CACHE = {}
_CACHE_TIMESTAMPS = {}

def cache_api_call(expire_hours=24):
    """
    Cache decorator for API calls
    Think of it as saving your homework so you don't have to redo it
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name + arguments
            cache_key = f"{func.__name__}:{json.dumps(args, sort_keys=True)}"
            
            # Check if cached and still fresh
            if cache_key in _API_CACHE and cache_key in _CACHE_TIMESTAMPS:
                age_hours = (datetime.now() - _CACHE_TIMESTAMPS[cache_key]).total_seconds() / 3600
                
                if age_hours < expire_hours:
                    print(f"  💾 CACHE HIT: {func.__name__} (age: {age_hours:.1f}h)")
                    return _API_CACHE[cache_key]
                else:
                    # Expired - remove it
                    print(f"  ⏰ CACHE EXPIRED: {func.__name__}")
                    del _API_CACHE[cache_key]
                    del _CACHE_TIMESTAMPS[cache_key]
            
            # Not cached or expired - call the actual function
            print(f"  🔍 CACHE MISS: {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cache the result
            _API_CACHE[cache_key] = result
            _CACHE_TIMESTAMPS[cache_key] = datetime.now()
            
            return result
        return wrapper
    return decorator
```

Now **WRAP** your existing fetch functions. Find these functions and add the decorator:

```python
# BEFORE:
def fetch_company_and_cashflows(ticker: str):
    # ... existing code ...

# AFTER:
@cache_api_call(expire_hours=24)  # ← ADD THIS LINE
def fetch_company_and_cashflows(ticker: str):
    # ... existing code ...


# Do the same for:
@cache_api_call(expire_hours=24)
def fetch_esg_data(ticker: str):
    # ... existing code ...

@cache_api_call(expire_hours=24)
def fetch_from_yahoo(ticker: str):
    # ... existing code ...
```

**Test it:**
```python
# Analyze AAPL twice in a row:
# First time: Should see "CACHE MISS" in logs
# Second time: Should see "CACHE HIT" in logs
```

---

## 🔧 Implementation 3: Database Migration to PostgreSQL (15 minutes)

**Step 1:** Replace your `db.py` completely with this:

```python
"""
Production-ready database configuration
Works with both SQLite (dev) and PostgreSQL (production)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# Detect environment
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'
DATABASE_URL = os.environ.get('DATABASE_URL')

# Fix Render's postgres:// URL (SQLAlchemy needs postgresql://)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Development: SQLite (for local testing)
if not DATABASE_URL or not IS_PRODUCTION:
    DATABASE_URL = "sqlite:///valuations.sqlite"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
    print(f"📊 Using SQLite: {DATABASE_URL}")
else:
    # Production: PostgreSQL (for Render)
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    print(f"🐘 Using PostgreSQL (production)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database init failed: {e}")
        raise

def get_session():
    """Get a new database session"""
    return SessionLocal()

# Initialize on import
init_db()
```

**Step 2:** Update `requirements.txt`:

```txt
# Add this line to your requirements.txt:
psycopg2-binary>=2.9
```

**Step 3:** Test locally:
```bash
pip install psycopg2-binary
python dcf_model.py
# Should see: "📊 Using SQLite: sqlite:///valuations.sqlite"
```

**Step 4:** In Render dashboard, DATABASE_URL will auto-populate. Your code will automatically switch to PostgreSQL!

---

## 🔧 Implementation 4: "Show Your Work" Button (20 minutes)

Add this route to `dcf_model.py`:

```python
@app.route('/api/explain', methods=['POST'])
def explain_calculation():
    """
    Return educational step-by-step explanation of DCF calculation
    This is the "show your work" feature
    """
    data = request.json
    results = data.get('results', {})
    
    company = results.get('company_data', {})
    hist = results.get('historical_metrics', {})
    wacc_results = results.get('wacc_results', {})
    assumptions = results.get('assumptions', {})
    
    explanation = {
        'sections': [
            {
                'title': '📦 Step 1: Gathering Data',
                'items': [
                    {
                        'label': 'Company Name',
                        'value': company.get('company_name'),
                        'explanation': 'The company we are analyzing'
                    },
                    {
                        'label': 'Current Stock Price',
                        'value': f"${company.get('current_stock_price', 0):.2f}",
                        'explanation': 'What the market THINKS the stock is worth'
                    },
                    {
                        'label': 'Shares Outstanding',
                        'value': f"{company.get('shares_outstanding', 0):.1f}M",
                        'explanation': 'Total number of shares in existence'
                    }
                ]
            },
            {
                'title': '💰 Step 2: Calculate Free Cash Flow',
                'formula': 'FCF = Operating Cash Flow - CapEx',
                'items': [
                    {
                        'label': 'Operating Cash Flow (TTM)',
                        'value': f"${hist.get('ttm_operating_cf', 0):.1f}M",
                        'explanation': 'Cash from core business operations'
                    },
                    {
                        'label': 'Capital Expenditures (TTM)',
                        'value': f"${hist.get('ttm_capex', 0):.1f}M",
                        'explanation': 'Money spent on equipment, buildings, etc.'
                    },
                    {
                        'label': 'Free Cash Flow (TTM)',
                        'value': f"${hist.get('ttm_fcf', 0):.1f}M",
                        'calculation': f"${hist.get('ttm_operating_cf', 0):.1f}M + (${hist.get('ttm_capex', 0):.1f}M)",
                        'explanation': 'Cash available to investors after maintaining the business'
                    }
                ]
            },
            {
                'title': '🎯 Step 3: Calculate WACC (Discount Rate)',
                'formula': 'WACC = (E/V × Re) + (D/V × Rd × (1-T))',
                'items': [
                    {
                        'label': 'Cost of Equity (Re)',
                        'value': f"{wacc_results.get('cost_of_equity', 0):.2%}",
                        'calculation': f"Rf({assumptions.get('risk_free_rate', 0):.2%}) + Beta({assumptions.get('beta', 0):.2f}) × MRP({assumptions.get('market_risk_premium', 0):.2%})",
                        'explanation': 'Return shareholders expect for the risk they take'
                    },
                    {
                        'label': 'After-Tax Cost of Debt',
                        'value': f"{wacc_results.get('after_tax_cost_debt', 0):.2%}",
                        'calculation': f"{assumptions.get('cost_of_debt', 0):.2%} × (1 - {assumptions.get('tax_rate', 0):.2%})",
                        'explanation': 'Cost of debt after tax deduction benefit'
                    },
                    {
                        'label': 'WACC',
                        'value': f"{wacc_results.get('wacc', 0):.2%}",
                        'calculation': f"({wacc_results.get('equity_weight', 0):.2f} × {wacc_results.get('cost_of_equity', 0):.2%}) + ({wacc_results.get('debt_weight', 0):.2f} × {wacc_results.get('after_tax_cost_debt', 0):.2%})",
                        'explanation': 'Blended cost of capital from equity and debt'
                    }
                ]
            },
            {
                'title': '🔮 Step 4: Project Future Cash Flows',
                'explanation': 'We project 5 years of future cash flows based on growth assumptions',
                'items': []
            },
            {
                'title': '⏰ Step 5: Discount to Present Value',
                'formula': 'PV = FV ÷ (1 + WACC)^n',
                'explanation': 'Convert future cash flows to today\'s dollars',
                'items': []
            },
            {
                'title': '♾️ Step 6: Terminal Value',
                'formula': 'TV = FCF(Year 6) ÷ (WACC - g)',
                'explanation': 'Value of all cash flows beyond Year 5',
                'items': [
                    {
                        'label': 'Terminal Value',
                        'value': f"${results.get('terminal_value', 0):.1f}M",
                        'explanation': 'Represents ~70% of total value!'
                    },
                    {
                        'label': 'PV of Terminal Value',
                        'value': f"${results.get('pv_terminal_value', 0):.1f}M",
                        'explanation': 'Terminal value discounted to today'
                    }
                ]
            },
            {
                'title': '🎯 Step 7: Calculate Intrinsic Value',
                'items': [
                    {
                        'label': 'Enterprise Value',
                        'value': f"${results.get('enterprise_value_dcf', 0):.1f}M",
                        'explanation': 'Sum of all discounted cash flows'
                    },
                    {
                        'label': 'Equity Value',
                        'value': f"${results.get('equity_value', 0):.1f}M",
                        'calculation': f"${results.get('enterprise_value_dcf', 0):.1f}M - ${company.get('total_debt', 0):.1f}M + ${company.get('cash', 0):.1f}M",
                        'explanation': 'Value for shareholders after accounting for debt'
                    },
                    {
                        'label': 'Intrinsic Value Per Share',
                        'value': f"${results.get('intrinsic_value_per_share', 0):.2f}",
                        'calculation': f"${results.get('equity_value', 0):.1f}M ÷ {company.get('shares_outstanding', 0):.1f}M shares",
                        'explanation': 'What each share is truly worth based on DCF'
                    }
                ]
            }
        ],
        'key_assumptions': {
            'Growth Rates': assumptions.get('revenue_growth_rates', []),
            'Perpetual Growth': f"{assumptions.get('perpetual_growth_rate', 0):.1%}",
            'Tax Rate': f"{assumptions.get('tax_rate', 0):.1%}",
            'Risk-Free Rate': f"{assumptions.get('risk_free_rate', 0):.1%}",
            'Market Risk Premium': f"{assumptions.get('market_risk_premium', 0):.1%}"
        },
        'final_verdict': {
            'intrinsic_value': f"${results.get('intrinsic_value_per_share', 0):.2f}",
            'market_price': f"${company.get('current_stock_price', 0):.2f}",
            'upside': f"{results.get('upside_pct', 0):.1f}%",
            'recommendation': 'BUY' if results.get('upside_pct', 0) > 15 else ('HOLD' if results.get('upside_pct', 0) > -10 else 'SELL')
        }
    }
    
    return jsonify(explanation)
```

Add this button to your **HTML** (in `index_input.html`, around line 700):

```html
<!-- Add this after the "Analyze Stock" button -->
<button class="button" onclick="showExplanation()" style="margin-top: 15px; background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
    📚 Show Step-by-Step Explanation
</button>
```

Add this JavaScript function:

```javascript
async function showExplanation() {
    if (!latestResults) {
        showAlert('Run an analysis first!');
        return;
    }
    
    try {
        const response = await fetch(apiUrl('/api/explain'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({results: latestResults})
        });
        
        const explanation = await response.json();
        
        // Display in a modal or new section
        displayExplanation(explanation);
    } catch (error) {
        showAlert('Error generating explanation: ' + error.message);
    }
}

function displayExplanation(explanation) {
    let html = '<div class="section"><h2 class="section-title">📚 Step-by-Step Calculation Walkthrough</h2>';
    
    explanation.sections.forEach(section => {
        html += `<h3 style="color: #1e3c72; margin: 20px 0 10px;">${section.title}</h3>`;
        if (section.formula) {
            html += `<div style="background: #e7f3ff; padding: 10px; border-radius: 8px; margin: 10px 0; font-family: monospace;">${section.formula}</div>`;
        }
        if (section.explanation) {
            html += `<p style="color: #666;">${section.explanation}</p>`;
        }
        
        section.items.forEach(item => {
            html += `<div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">`;
            html += `<strong>${item.label}:</strong> ${item.value}<br>`;
            if (item.calculation) {
                html += `<span style="color: #667eea;">→ ${item.calculation}</span><br>`;
            }
            html += `<span style="color: #666; font-size: 0.9em;">${item.explanation}</span>`;
            html += `</div>`;
        });
    });
    
    html += '</div>';
    document.getElementById('results-container').innerHTML += html;
}
```

---

## ✅ Quick Testing Checklist

After implementing the above, test these:

```bash
# 1. Health Check
curl http://localhost:5000/api/health

# 2. Analyze with Caching
curl -X POST http://localhost:5000/api/analyze -H "Content-Type: application/json" -d '{"ticker":"AAPL"}'
# Run again immediately - should see cache hit in logs

# 3. Step-by-Step Explanation
# (Click the button in the UI after running an analysis)

# 4. Database (check it created tables)
sqlite3 valuations.sqlite ".schema"
# Should show: CREATE TABLE valuation_runs ...
```

---

## 🎯 Next Steps After Implementation

1. **Commit to Git:**
```bash
git add .
git commit -m "Add health check, caching, and educational features"
git push
```

2. **Deploy to Render:**
- Push to GitHub
- Render auto-deploys from `main` branch (if you set up render.yaml)
- Check logs: `https://dashboard.render.com`

3. **Set Environment Variables in Render:**
- Go to dashboard → Your service → Environment
- Add: `ALPHAVANTAGE_API_KEY`, `NEWS_API_KEY`, `FLASK_ENV=production`

4. **Monitor:**
- Set up UptimeRobot monitoring your health check endpoint
- Check logs daily for first week
- Track usage and cache hit rates

---

That's it! You now have:
✅ Health monitoring
✅ API caching (saves rate limits)
✅ Database that works in production
✅ Educational "Show Your Work" feature

Deploy with confidence! 🚀
