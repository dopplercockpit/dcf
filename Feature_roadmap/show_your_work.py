"""
"Show Your Work" Feature - Educational Step-by-Step Calculations

This is like having a finance professor standing behind you saying
"Now explain WHY you did that calculation" after every step.
Students actually learn better when they see the derivation, not just
the final answer.

Think of it as the "annotated playbook" for DCF analysis.
"""

def generate_calculation_walkthrough(results):
    """
    Generate a detailed, educational walkthrough of ALL calculations
    
    This transforms the black-box DCF into a glass-box where every
    assumption, calculation, and formula is visible and explained.
    """
    
    walkthrough = {
        'sections': []
    }
    
    # ============================================================
    # SECTION 1: GATHERING THE INGREDIENTS
    # ============================================================
    company = results.get('company_data', {})
    historical = results.get('historical_data', {})
    assumptions = results.get('assumptions', {})
    
    walkthrough['sections'].append({
        'title': '📦 Step 1: Gathering Our Ingredients',
        'explanation': '''
        Before we cook our DCF analysis, we need to gather all our ingredients.
        Think of this like mise en place in cooking - getting everything ready
        before you start the actual cooking process.
        ''',
        'steps': [
            {
                'title': 'Company Fundamentals',
                'data': {
                    'Company Name': company.get('company_name'),
                    'Stock Price (Today)': f"${company.get('current_stock_price', 0):.2f}",
                    'Shares Outstanding': f"{company.get('shares_outstanding', 0):.1f}M shares",
                    'Total Debt': f"${company.get('total_debt', 0):.1f}M",
                    'Cash on Hand': f"${company.get('cash', 0):.1f}M"
                },
                'why_it_matters': '''
                These are the basic facts about the company. The stock price tells us
                what the MARKET thinks the company is worth. Our job with DCF is to
                figure out what the company is ACTUALLY worth, and see if the market
                is right or wrong.
                '''
            }
        ]
    })
    
    # ============================================================
    # SECTION 2: CALCULATING FREE CASH FLOW
    # ============================================================
    hist_metrics = results.get('historical_metrics', {})
    ttm_ocf = hist_metrics.get('ttm_operating_cf', 0)
    ttm_capex = hist_metrics.get('ttm_capex', 0)
    ttm_fcf = hist_metrics.get('ttm_fcf', 0)
    
    walkthrough['sections'].append({
        'title': '💰 Step 2: Calculating Free Cash Flow (The Money That Matters)',
        'explanation': '''
        Free Cash Flow is the REAL money a company generates. It's like your 
        paycheck AFTER paying rent, groceries, and other necessities. This is
        the money that could be paid to investors or reinvested in growth.
        
        Formula: FCF = Operating Cash Flow - Capital Expenditures
        
        Why? Because Operating Cash Flow is all the cash from running the business,
        but CapEx (Capital Expenditures) is money we MUST spend to maintain/grow
        the business (like buying new equipment, buildings, etc).
        ''',
        'calculation': {
            'formula': 'FCF = Operating CF - CapEx',
            'step_by_step': [
                {
                    'step': 'Operating Cash Flow (TTM)',
                    'value': f"${ttm_ocf:.1f}M",
                    'explanation': 'Cash generated from core business operations over last 12 months'
                },
                {
                    'step': 'Capital Expenditures (TTM)',
                    'value': f"${ttm_capex:.1f}M",
                    'explanation': 'Money spent on physical assets (shown as negative)'
                },
                {
                    'step': 'Free Cash Flow (TTM)',
                    'value': f"${ttm_fcf:.1f}M",
                    'formula_shown': f"${ttm_ocf:.1f}M + (${ttm_capex:.1f}M) = ${ttm_fcf:.1f}M",
                    'explanation': 'This is the actual cash available to investors'
                }
            ]
        },
        'real_world_analogy': '''
        Imagine you run a food truck:
        - Operating CF = Money from selling tacos ($10,000/month)
        - CapEx = Money to repair the truck ($2,000/month)
        - FCF = Money left over ($8,000/month) ← This is what matters!
        '''
    })
    
    # ============================================================
    # SECTION 3: CALCULATING WACC (THE DISCOUNT RATE)
    # ============================================================
    wacc_results = results.get('wacc_results', {})
    wacc = wacc_results.get('wacc', 0)
    cost_of_equity = wacc_results.get('cost_of_equity', 0)
    cost_of_debt = assumptions.get('cost_of_debt', 0)
    tax_rate = assumptions.get('tax_rate', 0)
    equity_weight = wacc_results.get('equity_weight', 0)
    debt_weight = wacc_results.get('debt_weight', 0)
    
    walkthrough['sections'].append({
        'title': '🎯 Step 3: WACC - The Hurdle Rate (Cost of Capital)',
        'explanation': '''
        WACC (Weighted Average Cost of Capital) is the rate of return that
        investors DEMAND for giving their money to this company.
        
        Think of it like interest on a loan - except here, the "loan" is
        money from both stockholders AND bondholders. We need to calculate
        the blended rate that satisfies both groups.
        
        This becomes our "discount rate" - it tells us how much future
        money is worth in today's dollars.
        ''',
        'calculation': {
            'formula': 'WACC = (E/V × Re) + (D/V × Rd × (1-T))',
            'variables': {
                'E/V': {'value': f'{equity_weight:.3f}', 'meaning': 'Weight of Equity (what % is stock)'},
                'Re': {'value': f'{cost_of_equity:.3%}', 'meaning': 'Cost of Equity (what stockholders demand)'},
                'D/V': {'value': f'{debt_weight:.3f}', 'meaning': 'Weight of Debt (what % is bonds/loans)'},
                'Rd': {'value': f'{cost_of_debt:.3%}', 'meaning': 'Cost of Debt (interest rate on debt)'},
                'T': {'value': f'{tax_rate:.1%}', 'meaning': 'Tax Rate (debt gives tax benefits!)'}
            },
            'step_by_step': [
                {
                    'step': '3a. Calculate Cost of Equity (Re)',
                    'formula': 'Re = Rf + (Beta × Market Risk Premium)',
                    'values': {
                        'Risk-free rate (Rf)': f"{assumptions.get('risk_free_rate', 0):.1%}",
                        'Beta': f"{assumptions.get('beta', 0):.2f}",
                        'Market Risk Premium': f"{assumptions.get('market_risk_premium', 0):.1%}"
                    },
                    'result': f"{cost_of_equity:.3%}",
                    'explanation': '''
                    Cost of Equity = What stockholders demand as return.
                    We use CAPM (Capital Asset Pricing Model) which says:
                    "Risk-free rate" (Treasury bonds) + "Risk premium" (extra for stock risk)
                    '''
                },
                {
                    'step': '3b. Calculate After-Tax Cost of Debt',
                    'formula': 'Rd × (1 - T)',
                    'calculation': f"{cost_of_debt:.1%} × (1 - {tax_rate:.1%}) = {cost_of_debt * (1-tax_rate):.3%}",
                    'explanation': '''
                    Debt is TAX DEDUCTIBLE! Companies can write off interest payments
                    on their taxes, so the "true" cost of debt is lower than the
                    interest rate. It's like getting a discount on your loan!
                    '''
                },
                {
                    'step': '3c. Blend Equity and Debt Costs',
                    'formula': 'WACC = (E/V × Re) + (D/V × Rd × (1-T))',
                    'calculation': f"({equity_weight:.3f} × {cost_of_equity:.3%}) + ({debt_weight:.3f} × {cost_of_debt * (1-tax_rate):.3%})",
                    'result': f"{wacc:.3%}",
                    'explanation': '''
                    We blend the costs based on how much of each the company uses.
                    If 70% funded by stock and 30% by debt, we weight accordingly.
                    '''
                }
            ]
        },
        'real_world_analogy': '''
        Imagine you're buying a house:
        - 20% down payment = Equity (your money)
        - 80% mortgage = Debt (bank's money at 5% interest)
        - Your "WACC" is the blended cost of both sources
        
        If the house appreciates at 6% per year but your WACC is 4.5%,
        you're making 1.5% profit! That's the idea here.
        '''
    })
    
    # ============================================================
    # SECTION 4: PROJECTING FUTURE CASH FLOWS
    # ============================================================
    projected_fcf = results.get('projected_fcf', [])
    growth_rates = assumptions.get('revenue_growth_rates', [])
    
    projection_steps = []
    base_fcf = ttm_fcf
    for year, (fcf, growth) in enumerate(zip(projected_fcf, growth_rates), 1):
        if year == 1:
            calculation = f"${base_fcf:.1f}M × (1 + {growth:.1%}) = ${fcf:.1f}M"
        else:
            calculation = f"${projected_fcf[year-2]:.1f}M × (1 + {growth:.1%}) = ${fcf:.1f}M"
        
        projection_steps.append({
            'year': year,
            'growth_rate': f"{growth:.1%}",
            'fcf': f"${fcf:.1f}M",
            'calculation': calculation,
            'explanation': f"We assume the business grows by {growth:.1%} this year"
        })
    
    walkthrough['sections'].append({
        'title': '🔮 Step 4: Projecting Future Cash Flows',
        'explanation': '''
        Now we play fortune-teller! We project what the company's cash flows
        will look like for the next 5 years.
        
        Why 5 years? It's a balance:
        - Too short: We miss long-term value
        - Too long: Predictions get unreliable (nobody knows what 2050 looks like!)
        
        We assume growth rates that typically start higher and taper down
        (most companies can't grow 20% forever - eventually they get big
        enough that physics stops them).
        ''',
        'projections': projection_steps,
        'reality_check': '''
        ⚠️ These are ASSUMPTIONS! The future is uncertain. This is why
        analysts do sensitivity analysis - they test "what if we're wrong?"
        A good DCF acknowledges uncertainty rather than hiding it.
        '''
    })
    
    # ============================================================
    # SECTION 5: DISCOUNTING TO PRESENT VALUE
    # ============================================================
    pv_fcf = results.get('pv_fcf', [])
    discount_steps = []
    
    for year, (fcf, pv) in enumerate(zip(projected_fcf, pv_fcf), 1):
        discount_factor = 1 / ((1 + wacc) ** year)
        calculation = f"${fcf:.1f}M ÷ (1 + {wacc:.3%})^{year} = ${pv:.1f}M"
        
        discount_steps.append({
            'year': year,
            'future_fcf': f"${fcf:.1f}M",
            'discount_factor': f"{discount_factor:.4f}",
            'present_value': f"${pv:.1f}M",
            'calculation': calculation,
            'explanation': f"Money {year} years from now is worth less today"
        })
    
    walkthrough['sections'].append({
        'title': '⏰ Step 5: Time-Traveling Money (Present Value)',
        'explanation': '''
        A dollar today is worth MORE than a dollar tomorrow. Why?
        
        1. You could invest that dollar today and have MORE tomorrow
        2. Inflation erodes purchasing power
        3. Future cash is UNCERTAIN (bird in hand > bird in bush)
        
        We "discount" future cash flows back to today using our WACC as
        the discount rate. This is like time-traveling money backwards.
        
        Formula: PV = FV ÷ (1 + r)^n
        Where:
        - PV = Present Value (what it's worth today)
        - FV = Future Value (what we'll get in the future)
        - r = Discount rate (WACC)
        - n = Number of years
        ''',
        'discounting_steps': discount_steps,
        'real_world_analogy': '''
        Would you rather have $100 today or $100 in 5 years?
        Obviously today! But what about $100 today vs $150 in 5 years?
        Now you need to calculate: Is that extra $50 worth the wait?
        
        That's what discounting answers: It tells us the "fair" value
        today for money we'll receive in the future.
        '''
    })
    
    # ============================================================
    # SECTION 6: TERMINAL VALUE (THE BIG KAHUNA)
    # ============================================================
    terminal_value = results.get('terminal_value', 0)
    pv_terminal = results.get('pv_terminal_value', 0)
    perpetual_growth = assumptions.get('perpetual_growth_rate', 0)
    final_fcf = projected_fcf[-1] if projected_fcf else 0
    
    walkthrough['sections'].append({
        'title': '♾️ Step 6: Terminal Value (The Infinity Stone)',
        'explanation': '''
        Here's the tricky part: Companies don't stop existing after Year 5!
        
        Terminal Value captures ALL the cash flows AFTER our 5-year forecast.
        It's typically 60-80% of the total value, so this number is HUGE!
        
        We use the "Perpetuity Growth" method which assumes the company
        will grow at a steady, sustainable rate FOREVER (like 2-3% per year,
        matching GDP growth).
        
        Formula: TV = FCF(Year 6) ÷ (WACC - g)
        Where g = perpetual growth rate
        ''',
        'calculation': {
            'step_by_step': [
                {
                    'step': '6a. Calculate Year 6 FCF',
                    'formula': f'FCF(Year 5) × (1 + g)',
                    'calculation': f"${final_fcf:.1f}M × (1 + {perpetual_growth:.1%}) = ${final_fcf * (1 + perpetual_growth):.1f}M",
                    'explanation': 'We project one more year of growth to get Year 6'
                },
                {
                    'step': '6b. Calculate Terminal Value',
                    'formula': 'TV = FCF(Year 6) ÷ (WACC - g)',
                    'calculation': f"${final_fcf * (1 + perpetual_growth):.1f}M ÷ ({wacc:.3%} - {perpetual_growth:.1%}) = ${terminal_value:.1f}M",
                    'explanation': 'This is the value of ALL future cash flows beyond Year 5'
                },
                {
                    'step': '6c. Discount Terminal Value to Today',
                    'formula': 'PV(TV) = TV ÷ (1 + WACC)^5',
                    'calculation': f"${terminal_value:.1f}M ÷ (1 + {wacc:.3%})^5 = ${pv_terminal:.1f}M",
                    'explanation': 'Time-travel this future value back to today'
                }
            ]
        },
        'warning': '''
        ⚠️ SENSITIVITY ALERT! Terminal value is EXTREMELY sensitive to:
        1. The perpetual growth rate (g): 1% difference = huge $ impact
        2. The discount rate (WACC): Even 0.5% change matters
        
        This is why DCF is both powerful and dangerous - small assumption
        changes create massive valuation swings!
        '''
    })
    
    # ============================================================
    # SECTION 7: ENTERPRISE VALUE TO EQUITY VALUE
    # ============================================================
    enterprise_value = results.get('enterprise_value_dcf', 0)
    equity_value = results.get('equity_value', 0)
    total_debt = company.get('total_debt', 0)
    cash = company.get('cash', 0)
    
    walkthrough['sections'].append({
        'title': '🏢 Step 7: From Enterprise Value to Equity Value',
        'explanation': '''
        We've calculated "Enterprise Value" - the value of the entire business.
        But stockholders don't own the entire business! They own what's LEFT
        after paying off debt.
        
        Think of buying a house:
        - House value = $500,000 (Enterprise Value)
        - Mortgage owed = $300,000 (Debt)
        - Cash in escrow = $20,000 (Cash)
        - Your equity = $500,000 - $300,000 + $20,000 = $220,000
        
        Same concept here!
        ''',
        'calculation': {
            'formula': 'Equity Value = Enterprise Value - Total Debt + Cash',
            'step_by_step': [
                {
                    'component': 'Enterprise Value (from DCF)',
                    'value': f"${enterprise_value:.1f}M",
                    'explanation': 'Sum of all discounted cash flows (including terminal value)'
                },
                {
                    'component': '- Total Debt',
                    'value': f"${total_debt:.1f}M",
                    'explanation': 'Debt holders get paid first, so we subtract this'
                },
                {
                    'component': '+ Cash',
                    'value': f"${cash:.1f}M",
                    'explanation': 'Cash belongs to shareholders, so we add it back'
                },
                {
                    'component': '= Equity Value',
                    'value': f"${equity_value:.1f}M",
                    'explanation': 'This is what stockholders actually own'
                }
            ]
        }
    })
    
    # ============================================================
    # SECTION 8: INTRINSIC VALUE PER SHARE
    # ============================================================
    shares_outstanding = company.get('shares_outstanding', 0)
    intrinsic_value = results.get('intrinsic_value_per_share', 0)
    current_price = company.get('current_stock_price', 0)
    upside = results.get('upside_pct', 0)
    
    walkthrough['sections'].append({
        'title': '🎯 Step 8: The Final Answer (Intrinsic Value Per Share)',
        'explanation': '''
        Now we just divide the equity value by the number of shares
        to get the value PER SHARE. This is what you'd compare to
        the current stock price to decide if it's a good deal.
        ''',
        'calculation': {
            'formula': 'Intrinsic Value Per Share = Equity Value ÷ Shares Outstanding',
            'calculation': f"${equity_value:.1f}M ÷ {shares_outstanding:.1f}M shares = ${intrinsic_value:.2f}/share",
            'comparison': {
                'intrinsic_value': f"${intrinsic_value:.2f}",
                'current_price': f"${current_price:.2f}",
                'difference': f"${intrinsic_value - current_price:.2f}",
                'upside_pct': f"{upside:.1f}%"
            }
        },
        'interpretation': {
            'verdict': 'BUY' if upside > 15 else ('HOLD' if upside > -10 else 'SELL'),
            'explanation': f'''
            Based on our DCF analysis, the stock is worth ${intrinsic_value:.2f}
            but trading at ${current_price:.2f}.
            
            This means the market is {"undervaluing" if upside > 0 else "overvaluing"}
            the stock by {abs(upside):.1f}%.
            
            BUT REMEMBER: This is based on OUR assumptions! If our growth rates
            are too optimistic, or our WACC is too low, we could be wrong.
            Always do sensitivity analysis and compare to other valuation methods!
            '''
        }
    })
    
    # ============================================================
    # FINAL WISDOM
    # ============================================================
    walkthrough['sections'].append({
        'title': '🎓 Final Lessons: What We Learned',
        'key_takeaways': [
            '''DCF is POWERFUL: It forces you to think about the fundamental drivers
            of value - cash flows, growth, and risk.''',
            
            '''DCF is DANGEROUS: Small changes in assumptions lead to huge changes
            in valuation. Never trust a single DCF number blindly.''',
            
            '''DCF is EDUCATIONAL: Even if the final number is wrong, going through
            the process teaches you to think like an investor.''',
            
            '''DCF is ONE TOOL: Always use multiple valuation methods (P/E ratios,
            comparable companies, etc.) and triangulate to the truth.''',
            
            '''DCF requires JUDGMENT: The formulas are mathematical, but the inputs
            (growth rates, terminal value) require business judgment and research.'''
        ],
        'next_steps': [
            'Run sensitivity analysis: What if growth is 1% lower?',
            'Compare to peer companies: Is this valuation reasonable?',
            'Read the annual report: Do our assumptions match management guidance?',
            'Check analyst reports: What do professionals think?',
            'Monitor over time: Track if our predictions come true!'
        ]
    })
    
    return walkthrough


# Usage in the Flask app:
# 
# @app.route('/api/walkthrough', methods=['POST'])
# def get_walkthrough():
#     data = request.json
#     results = data.get('results')
#     walkthrough = generate_calculation_walkthrough(results)
#     return jsonify(walkthrough)
