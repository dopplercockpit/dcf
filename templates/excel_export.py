# --- ADD THESE IMPORTS AT THE TOP OF dcf_model.py ---
import pandas as pd
import time

# --- ADD THIS FUNCTION ABOVE THE DCFModel CLASS ---
def save_excel_report(ticker, company_data, historical_data, financials_raw):
    """
    Saves the static data (non-calculated) to an Excel file 
    in a 'reports' folder.
    """
    try:
        # Create reports directory if not exists
        if not os.path.exists('reports'):
            os.makedirs('reports')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{ticker}_{timestamp}_Financials.xlsx"

        # 1. Prepare Overview Data
        df_overview = pd.DataFrame([company_data])
        
        # 2. Prepare Historical Data
        # Transpose list of lists into a clean DataFrame
        hist_dict = {
            'Quarter': historical_data['quarters'],
            'Operating Cash Flow ($M)': historical_data['operating_cash_flow'],
            'CapEx ($M)': historical_data['capex'],
            'Net Income ($M)': historical_data['net_income']
        }
        df_historical = pd.DataFrame(hist_dict)

        # 3. Prepare Raw Balance Sheet Data (from your recent update)
        # Check if raw_financials exists and has data
        raw_bs_data = []
        if financials_raw and 'raw_data' in financials_raw:
             for k, v in financials_raw['raw_data'].items():
                 raw_bs_data.append({'Item': k, 'Value': v})
        df_balance_sheet = pd.DataFrame(raw_bs_data)

        # Write to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_overview.to_excel(writer, sheet_name='Company Overview', index=False)
            df_historical.to_excel(writer, sheet_name='Historical Cash Flows', index=False)
            df_balance_sheet.to_excel(writer, sheet_name='Raw Balance Sheet', index=False)
            
        print(f"  💾 Data exported successfully to: {filename}")
        return filename
        
    except Exception as e:
        print(f"  ⚠️ Excel export failed: {e}")
        return None

# --- UPDATE THE analyze_ticker ROUTE ---
# Look for the existing analyze_ticker function and find the end 
# where 'results' is constructed. Add the excel call there.

@app.route('/api/analyze', methods=['POST'])
def analyze_ticker():
    # ... [Keep all existing code up until results dictionary is created] ...
    
        # [EXISTING CODE]
        results['company_data'] = company_data
        results['historical_data'] = historical_data
        results['assumptions'] = assumptions
        results['reddit_sentiment'] = reddit_data
        results['news_analysis'] = news_data
        results['data_quality'] = quality_report
        results['raw_financials'] = raw_financials
        
        # --- NEW CODE: GENERATE EXCEL ---
        excel_file = save_excel_report(ticker, company_data, historical_data, raw_financials)
        results['excel_file_path'] = excel_file
        # --------------------------------
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        # ... [Rest of existing code] ...