# Universal DCF Valuation Model

A web-based Discounted Cash Flow (DCF) analysis tool that automatically fetches company data from Alpha Vantage API and calculates intrinsic stock value.

## Features

- **One-click analysis**: Enter a ticker symbol and get complete DCF valuation
- **Automatic data fetching**: Company financials, stock price, and cash flow data from Alpha Vantage
- **Professional calculations**: WACC, projected cash flows, terminal value, and intrinsic value
- **Buy/Sell/Hold recommendations**: Based on market vs intrinsic value comparison
- **Customizable assumptions**: Override default values for advanced analysis

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Alpha Vantage API Key

1. Go to https://www.alphavantage.co/support/#api-key
2. Get a FREE API key (no credit card required)
3. Copy your API key

### 3. Set Environment Variable

**On Windows (PowerShell):**
```powershell
$env:ALPHAVANTAGE_API_KEY="your_api_key_here"
```

**On Windows (Command Prompt):**
```cmd
set ALPHAVANTAGE_API_KEY=your_api_key_here
```

**On Mac/Linux (Terminal):**
```bash
export ALPHAVANTAGE_API_KEY="your_api_key_here"
```

**Permanent Setup (Optional):**

To avoid setting the key every time, add it to your system environment variables:
- **Windows**: Search "Environment Variables" in Start menu → Add new System Variable
- **Mac/Linux**: Add `export ALPHAVANTAGE_API_KEY="your_key"` to ~/.bashrc or ~/.zshrc

### 4. Run the Application

```bash
python dcf_model.py
```

### 5. Open in Browser

Navigate to: **http://localhost:5000**

## How to Use

1. **Enter a ticker symbol** (e.g., AAPL, MSFT, GOOGL, TSLA)
2. **Click "Analyze Stock"**
3. **Wait a few seconds** while data is fetched
4. **View comprehensive DCF analysis**:
   - Market value vs Intrinsic value
   - Buy/Sell/Hold recommendation
   - Historical cash flows (12 quarters)
   - 5-year projections
   - WACC breakdown
   - Key metrics (IRR, EV/FCF, etc.)

### Advanced Settings (Optional)

Click "Advanced Settings" to customize:
- Tax rate (default: 21%)
- Risk-free rate (default: 4.5%)
- Market risk premium (default: 8%)
- Beta (auto-fetched from API)
- Cost of debt (default: 5%)
- Perpetual growth rate (default: 2.5%)
- Revenue growth rates for Years 1-5

## Troubleshooting

### Error: "Alpha Vantage API key is not configured"

**Solution**: Make sure you've set the environment variable:
```bash
echo $ALPHAVANTAGE_API_KEY  # Mac/Linux
echo %ALPHAVANTAGE_API_KEY%  # Windows CMD
```

If empty, set it following Step 3 above.

### Error: "Alpha Vantage rate limit"

**Solution**: Free API keys are limited to 25 requests/day and 5 requests/minute. Wait a minute and try again.

### Error: "Failed to fetch data for TICKER"

**Solutions**:
- Verify the ticker symbol is correct (US stocks only)
- Check your internet connection
- Ensure the API key is valid
- Try a different ticker (e.g., AAPL)

### Error: "Server returned non-JSON response"

**Solution**:
- Check the terminal/console where Flask is running for error messages
- Restart the Flask server
- Verify all dependencies are installed

## API Endpoints

- `GET /` - Main web interface
- `POST /api/analyze` - Fetch data and calculate DCF (requires ticker + optional assumptions)
- `GET /api/alpha_vantage?ticker=AAPL` - Fetch raw company data
- `POST /api/calculate` - Calculate DCF with provided data
- `GET /api/defaults` - Get default assumptions

## Example Usage

### Quick Analysis
```
1. Enter "AAPL" in the ticker field
2. Click "Analyze Stock"
3. View results
```

### Custom Analysis
```
1. Enter ticker symbol
2. Click "Advanced Settings"
3. Adjust assumptions (e.g., change growth rates)
4. Click "Analyze Stock"
```

## Technical Details

### Data Fetched from Alpha Vantage
- Company overview (name, shares outstanding, debt, cash, beta)
- Real-time stock price
- Quarterly cash flow statements (last 12 quarters)
- Operating cash flow, CapEx, and net income

### DCF Calculation Steps
1. Calculate Free Cash Flow (FCF = Operating CF + CapEx)
2. Project 5-year cash flows with growth rates
3. Calculate WACC (Weighted Average Cost of Capital)
4. Discount projected cash flows to present value
5. Calculate terminal value using perpetual growth method
6. Determine enterprise value and equity value
7. Calculate intrinsic value per share

## Notes

- **Free API Limits**: 25 requests/day, 5 requests/minute
- **US Stocks Only**: Alpha Vantage primarily covers US markets
- **Educational Purpose**: This tool is for educational/research purposes only. Not financial advice.
- **Data Accuracy**: Always verify calculations with multiple sources

## License

This project is for educational purposes only. Use at your own risk.
