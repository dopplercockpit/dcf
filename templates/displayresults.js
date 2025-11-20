function displayResults(results) {
    const container = document.getElementById('results-container');
    const companyInfo = results.company_data;
    const upside = results.upside_pct;
    const assumptions = results.assumptions;
    const waccData = results.wacc_results;

    // Helper to format percentages safely
    const fmtP = (num) => (num * 100).toFixed(1) + '%';
    const fmtM = (num) => '$' + num.toFixed(0) + 'M';

    // --- DYNAMIC TOOLTIP CONTENT GENERATORS ---

    // 1. Cost of Equity Breakdown: Rf + Beta * MRP
    const ke_formula = `
        <strong>CAPM Formula:</strong><br>
        Risk-Free (${fmtP(assumptions.risk_free_rate)}) + <br>
        [Beta (${assumptions.beta.toFixed(2)}) × MRP (${fmtP(assumptions.market_risk_premium)})]<br>
        <hr style="margin:5px 0; border-color:#555">
        = <strong>${fmtP(waccData.cost_of_equity)}</strong>
    `;

    // 2. WACC Breakdown
    const wacc_formula = `
        <strong>Equity Side:</strong> ${fmtP(waccData.equity_weight)} weight × ${fmtP(waccData.cost_of_equity)} cost<br>
        + <strong>Debt Side:</strong> ${fmtP(waccData.debt_weight)} weight × ${fmtP(assumptions.cost_of_debt)} cost × (1 - ${fmtP(assumptions.tax_rate)} Tax)<br>
        <hr style="margin:5px 0; border-color:#555">
        = <strong>${fmtP(waccData.wacc)}</strong>
    `;

    // 3. Terminal Value: (Final FCF * (1+g)) / (WACC - g)
    const last_fcf = results.projected_fcf[results.projected_fcf.length - 1];
    const term_formula = `
        <strong>Perpetual Growth Method:</strong><br>
        (Final FCF $${last_fcf.toFixed(0)}M × (1 + ${fmtP(assumptions.perpetual_growth_rate)})) <br>
        ÷ (WACC ${fmtP(waccData.wacc)} - Growth ${fmtP(assumptions.perpetual_growth_rate)})
    `;

    // 4. Intrinsic Value: (Equity Value / Shares)
    const intrinsic_formula = `
        <strong>Equity Value:</strong> ${fmtM(results.equity_value)}<br>
        ÷ <strong>Shares:</strong> ${companyInfo.shares_outstanding.toFixed(1)}M
    `;

    // 5. Equity Value Walkthrough: Enterprise Value + Cash - Debt
    const eq_val_formula = `
        <strong>Enterprise Value (DCF):</strong> ${fmtM(results.enterprise_value_dcf)}<br>
        + <strong>Cash:</strong> ${fmtM(companyInfo.cash)}<br>
        - <strong>Debt:</strong> ${fmtM(companyInfo.total_debt)}
    `;

    // ... [Keep your existing recommendation logic here] ...
    let recommendation, returnText, arrowHTML, arrowClass;
    if (upside >= 20) {
        recommendation = '🟢 STRONG BUY - Significantly undervalued';
        returnText = `Potential upside of ${upside.toFixed(1)}% to fair value`;
        arrowHTML = '↗'; arrowClass = 'arrow up';
    } else if (upside >= 10) {
        recommendation = '🟢 BUY - Moderately undervalued';
        returnText = `Potential upside of ${upside.toFixed(1)}% to fair value`;
        arrowHTML = '↗'; arrowClass = 'arrow up';
    } else if (upside >= -10) {
        recommendation = '🟡 HOLD - Fairly valued';
        returnText = `Trading near fair value (${upside.toFixed(1)}% ${upside >= 0 ? 'upside' : 'downside'})`;
        arrowHTML = '→'; arrowClass = 'arrow';
    } else {
        recommendation = '🔴 SELL / STRONG SELL';
        returnText = `Potential downside of ${Math.abs(upside).toFixed(1)}% to fair value`;
        arrowHTML = '↘'; arrowClass = 'arrow down';
    }

    container.innerHTML = `
        <div class="section">
            <h2 class="section-title">💰 Valuation Results: ${companyInfo.company_name} (${companyInfo.ticker})</h2>

            <div class="comparison">
                <div class="comparison-item">
                    <div class="comparison-label">Market Price</div>
                    <div class="comparison-value">$${results.current_market_value.toFixed(2)}</div>
                </div>
                <div class="${arrowClass}">${arrowHTML}</div>
                <div class="comparison-item">
                    <div class="comparison-label tooltip-container">
                        Intrinsic Value
                        <span class="tooltip-text">${intrinsic_formula}</span>
                    </div>
                    <div class="comparison-value">$${results.intrinsic_value_per_share.toFixed(2)}</div>
                </div>
            </div>

            <div class="info-box">
                <p><strong>Recommendation:</strong> ${recommendation}</p>
                <p><strong>Potential Return:</strong> ${returnText}</p>
            </div>

            <div class="results-grid">
                <div class="result-card ${upside >= 0 ? 'positive' : 'negative'}">
                    <div class="result-label">Upside/Downside</div>
                    <div class="result-value ${upside >= 0 ? 'positive' : 'negative'}">${(upside >= 0 ? '+' : '')}${upside.toFixed(1)}%</div>
                </div>
                <div class="result-card">
                    <div class="result-label tooltip-container">
                        WACC ⓘ
                        <span class="tooltip-text">${wacc_formula}</span>
                    </div>
                    <div class="result-value">${fmtP(waccData.wacc)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label tooltip-container">
                        Cost of Equity ⓘ
                        <span class="tooltip-text">${ke_formula}</span>
                    </div>
                    <div class="result-value">${fmtP(waccData.cost_of_equity)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">IRR</div>
                    <div class="result-value">${(results.irr * 100).toFixed(2)}%</div>
                </div>
            </div>

            <div class="results-grid" style="margin-top: 20px;">
                <div class="result-card">
                    <div class="result-label">Enterprise Value (DCF)</div>
                    <div class="result-value">${fmtM(results.enterprise_value_dcf)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label tooltip-container">
                        Equity Value ⓘ
                        <span class="tooltip-text">${eq_val_formula}</span>
                    </div>
                    <div class="result-value">${fmtM(results.equity_value)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label tooltip-container">
                        Terminal Value ⓘ
                        <span class="tooltip-text">${term_formula}</span>
                    </div>
                    <div class="result-value">${fmtM(results.terminal_value)}</div>
                </div>
                <div class="result-card">
                    <div class="result-label">EV/FCF Multiple</div>
                    <div class="result-value">${results.ev_fcf_multiple.toFixed(2)}x</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📈 Historical Performance</h2>
             <table>
                <thead>
                    <tr>
                        <th>Quarter</th>
                        <th>Operating CF ($M)</th>
                        <th>CapEx ($M)</th>
                        <th>Free Cash Flow ($M)</th>
                        <th>Net Income ($M)</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.historical_data.quarters.map((q, i) => `
                        <tr>
                            <td><strong>${q}</strong></td>
                            <td>${results.historical_data.operating_cash_flow[i].toFixed(0)}</td>
                            <td>${results.historical_data.capex[i].toFixed(0)}</td>
                            <td><strong>${results.historical_metrics.quarterly_fcf[i].toFixed(0)}</strong></td>
                            <td>${(results.historical_data.net_income[i] || 0).toFixed(0)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
         <div class="section">
            <h2 class="section-title">🔮 Projected Free Cash Flows (5-Year Forecast)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Projected FCF ($M)</th>
                        <th>Discount Factor</th>
                        <th>Present Value ($M)</th>
                        <th>Growth Rate</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.projected_fcf.map((fcf, i) => {
                        const year = i + 1;
                        const discount = 1 / Math.pow(1 + results.wacc_results.wacc, year);
                        const pv = results.pv_fcf[i];
                        const growth = results.assumptions.revenue_growth_rates[i];
                        return `
                            <tr>
                                <td><strong>Year ${year}</strong></td>
                                <td>${fcf.toFixed(2)}</td>
                                <td>${discount.toFixed(4)}</td>
                                <td><strong>${pv.toFixed(2)}</strong></td>
                                <td>${(growth * 100).toFixed(1)}%</td>
                            </tr>
                        `;
                    }).join('')}
                     <tr style="background-color: #e7f3ff; font-weight: bold;">
                        <td><strong>Terminal Value</strong></td>
                        <td>${results.terminal_value.toFixed(2)}</td>
                        <td>${(1 / Math.pow(1 + results.wacc_results.wacc, 5)).toFixed(4)}</td>
                        <td><strong>${results.pv_terminal_value.toFixed(2)}</strong></td>
                        <td>${(results.assumptions.perpetual_growth_rate * 100).toFixed(1)}%</td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}