# 🚀 Deployment Guide: From Localhost to Live

This guide walks you through deploying your DCF calculator to production.
Think of deployment like moving from your dorm room to an apartment - 
everything needs to work when other people start using it!

## 📋 Pre-Deployment Checklist

### 1. **Environment Variables** ✅
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual keys
nano .env  # or use your favorite editor

# Required:
ALPHAVANTAGE_API_KEY=your_actual_key_here

# Optional but recommended:
NEWS_API_KEY=your_news_key_here
SECRET_KEY=generate_with_python_secrets
```

### 2. **Test Locally First** ✅
```bash
# Install dependencies
pip install -r requirements_production.txt

# Run local server
python dcf_model.py

# Test these endpoints:
curl http://localhost:5000/api/health  # Should return {"status": "healthy"}
curl -X POST http://localhost:5000/api/analyze -H "Content-Type: application/json" -d '{"ticker":"AAPL"}'
```

### 3. **Update Requirements** ✅
Replace your `requirements.txt` with `requirements_production.txt`:
```bash
cp requirements_production.txt requirements.txt
```

## 🎯 Option 1: Deploy to Render.com (Recommended)

Render is like the "easy button" for deployment - it handles all the scary stuff.

### Step 1: Prepare Your Code
```bash
# Make sure these files exist in your root directory:
# ✓ dcf_model.py
# ✓ requirements.txt
# ✓ render.yaml
# ✓ .env.example (for documentation)

# Create .gitignore if you haven't already
echo ".env
.venv/
__pycache__/
*.pyc
*.sqlite" > .gitignore
```

### Step 2: Push to GitHub
```bash
git init
git add .
git commit -m "Initial deployment setup"
git branch -M main
git remote add origin https://github.com/yourusername/dcf-calculator.git
git push -u origin main
```

### Step 3: Deploy on Render
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml` automatically!
5. Set environment variables in the dashboard:
   - `ALPHAVANTAGE_API_KEY` = your_key_here
   - `NEWS_API_KEY` = your_key_here (optional)
6. Click "Apply" and wait 5-10 minutes

### Step 4: Test Your Deployment
```bash
# Your app will be at: https://dcf-calculator.onrender.com
curl https://dcf-calculator.onrender.com/api/health
```

## 🎯 Option 2: Deploy to Vercel (Alternative)

Vercel is great for hobby projects but requires some adjustments since
it's designed more for Node.js apps. Here's the workaround:

### Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "dcf_model.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "dcf_model.py"
    }
  ]
}
```

### Deploy:
```bash
npm i -g vercel
vercel --prod
```

## 🔧 Post-Deployment: Essential Monitoring

### 1. **Set Up Uptime Monitoring**
Use a free service like [UptimeRobot](https://uptimerobot.com):
- Monitor: `https://your-app.onrender.com/api/health`
- Check interval: Every 5 minutes
- Alert email: your@email.com

### 2. **Check Logs Regularly**
```bash
# Render logs (via dashboard or CLI)
render logs --service dcf-calculator --tail

# Look for these warning signs:
# ❌ "Database connection failed"
# ❌ "Alpha Vantage rate limit"
# ❌ "500 Internal Server Error"
```

### 3. **Set Up Error Tracking** (Optional but Awesome)
```python
# Add to requirements.txt:
sentry-sdk[flask]>=1.40

# Add to dcf_model.py (top):
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment=os.environ.get("FLASK_ENV", "development")
)
```

## 🐛 Troubleshooting Common Issues

### Issue: "Database connection failed"
**Problem:** PostgreSQL isn't initialized
**Solution:**
```bash
# Check Render dashboard → dcf-db → Make sure it's "Available"
# Check environment variable DATABASE_URL is set correctly
```

### Issue: "Alpha Vantage rate limit exceeded"
**Problem:** Too many students hitting the API at once
**Solution:**
1. Implement caching (see `caching_layer.py`)
2. Get multiple API keys (free tier allows multiple keys)
3. Upgrade to paid Alpha Vantage tier (~$50/month)

### Issue: "Application crash: Memory exceeded"
**Problem:** Render free tier has 512MB RAM limit
**Solution:**
1. Reduce worker count in render.yaml: `gunicorn -w 2` (instead of 4)
2. Implement request queuing
3. Upgrade to Starter plan ($7/month)

### Issue: "App sleeps after 15 minutes of inactivity"
**Problem:** Render free tier spins down inactive apps
**Solution:**
1. Set up uptime monitor (pings every 5 min)
2. Or upgrade to paid plan (always-on)

## 📊 Monitoring Your Deployment

### Key Metrics to Track:
1. **Response Time**: Should be < 5 seconds per analysis
2. **Error Rate**: Should be < 1% of requests
3. **API Call Usage**: Track Alpha Vantage quota (25/day free tier)
4. **Database Size**: Monitor growth (free tier: 1GB limit)

### Dashboard URLs:
- Render: https://dashboard.render.com/
- Health Check: https://your-app.onrender.com/api/health
- Status: https://your-app.onrender.com/api/status

## 🎓 For Students: Submission Checklist

When submitting your deployed app, include:

- [ ] Live URL (e.g., https://dcf-yourname.onrender.com)
- [ ] Health check passes (screenshot of /api/health)
- [ ] Test analysis (screenshot of AAPL analysis)
- [ ] Source code repository (GitHub link)
- [ ] Environment variables documented (in README)
- [ ] API call budget plan (how you'll stay under rate limits)

## 🚨 Security Reminders

1. **NEVER commit .env file** - Check .gitignore!
2. **Use environment variables** - Not hardcoded keys
3. **Enable CORS only for your domain** - Not "*"
4. **Rotate API keys** - If accidentally exposed
5. **Use HTTPS** - Render provides this automatically

## 🎉 Success Criteria

Your deployment is successful when:
- ✅ Health check returns 200 status
- ✅ Can analyze at least 3 different tickers
- ✅ Excel export downloads successfully
- ✅ Sentiment data loads (Reddit + News)
- ✅ Database persists valuations across restarts
- ✅ Error messages are user-friendly (no stack traces)

## 📚 Additional Resources

- [Render Python Docs](https://render.com/docs/deploy-flask)
- [Flask Production Checklist](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don't_Do_This)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)

---

**Need help?** Check the troubleshooting section above or ping me!
Remember: "It works on my machine" ≠ "It works in production"
But with this guide, you'll get there! 🚀
