/* ═══════════════════════════════════════════════════════════
   FX Risk Engine — Dashboard Application
   ═══════════════════════════════════════════════════════════ */

const API_BASE = '';  // Same origin

// ── State ────────────────────────────────────────────────
let state = {
    profiles: [],
    scenarios: [],
    activeProfile: null,
    charts: {},
    lastMCResult: null,
};

// ── Initialization ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    checkHealth();
    refreshProfiles();
    refreshScenarios();
});

// ── API Helpers ──────────────────────────────────────────
async function apiCall(method, endpoint, body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.detail || data.error || `API Error ${res.status}`);
    }
    return data;
}

function showLoading() {
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// ── Toast Notifications ──────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    toast.innerHTML = `<span style="font-weight:700;">${icons[type] || 'ℹ'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Navigation ───────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.dataset.section;
            navigateTo(section);
        });
    });
}

function navigateTo(section) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`[data-section="${section}"]`);
    if (navItem) navItem.classList.add('active');

    // Update sections
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    const sectionEl = document.getElementById(`section-${section}`);
    if (sectionEl) sectionEl.classList.add('active');

    // Update title
    const titles = {
        dashboard: 'Dashboard',
        exposures: 'Exposures',
        scenarios: 'Scenarios',
        pnl: 'P&L Analysis',
        sensitivity: 'Sensitivity Analysis',
        montecarlo: 'Monte Carlo Simulation',
        risk: 'Risk Report',
    };
    document.getElementById('page-title').textContent = titles[section] || section;

    // Refresh profile selectors
    updateProfileSelectors();
    updateScenarioSelectors();
}

// ── Health Check ─────────────────────────────────────────
async function checkHealth() {
    try {
        const data = await apiCall('GET', '/health');
        const dot = document.getElementById('api-status-dot');
        const text = document.getElementById('api-status-text');
        dot.className = 'status-dot online';
        text.textContent = 'Connected';
    } catch (e) {
        const dot = document.getElementById('api-status-dot');
        const text = document.getElementById('api-status-text');
        dot.className = 'status-dot offline';
        text.textContent = 'Disconnected';
    }
}

// ── Sample Dataset Loading ───────────────────────────────
async function loadSampleDataset() {
    showLoading();
    try {
        // Upload Company 1
        await apiCall('POST', '/exposures', {
            company_name: "Global Tech Corp",
            base_currency: "EUR",
            exposures: [
                { name: "US_Revenue", exp_type: "revenue", amount: 2500000, currency: "USD" },
                { name: "UK_Revenue", exp_type: "revenue", amount: 1200000, currency: "GBP" },
                { name: "JP_Revenue", exp_type: "revenue", amount: 85000000, currency: "JPY" },
                { name: "EU_Operations", exp_type: "cost", amount: 1800000, currency: "EUR" },
                { name: "US_Suppliers", exp_type: "cost", amount: 750000, currency: "USD" },
                { name: "JP_Components", exp_type: "cost", amount: 120000000, currency: "JPY" },
            ]
        });

        // Upload Company 2
        await apiCall('POST', '/exposures', {
            company_name: "Nordic Maritime AS",
            base_currency: "EUR",
            exposures: [
                { name: "US_Contracts", exp_type: "revenue", amount: 4000000, currency: "USD" },
                { name: "UK_Operations", exp_type: "revenue", amount: 800000, currency: "GBP" },
                { name: "EU_Fleet_Ops", exp_type: "cost", amount: 2500000, currency: "EUR" },
                { name: "JP_Equipment", exp_type: "cost", amount: 50000000, currency: "JPY" },
                { name: "US_Fuel", exp_type: "cost", amount: 1200000, currency: "USD" },
            ]
        });

        // Upload Company 3
        await apiCall('POST', '/exposures', {
            company_name: "Alpha Pharma GmbH",
            base_currency: "EUR",
            exposures: [
                { name: "US_Drug_Sales", exp_type: "revenue", amount: 8000000, currency: "USD" },
                { name: "UK_Licensing", exp_type: "revenue", amount: 2000000, currency: "GBP" },
                { name: "JP_Distribution", exp_type: "revenue", amount: 200000000, currency: "JPY" },
                { name: "EU_RnD", exp_type: "cost", amount: 5000000, currency: "EUR" },
                { name: "US_Clinical_Trials", exp_type: "cost", amount: 3000000, currency: "USD" },
                { name: "UK_Lab_Services", exp_type: "cost", amount: 500000, currency: "GBP" },
                { name: "JP_Manufacturing", exp_type: "cost", amount: 300000000, currency: "JPY" },
            ]
        });

        await refreshProfiles();
        await refreshScenarios();
        await updateDashboardMetrics();
        showToast('Sample dataset loaded — 3 companies with realistic FX exposures', 'success');
    } catch (e) {
        showToast(`Error loading dataset: ${e.message}`, 'error');
    }
    hideLoading();
}

// ── Profiles Management ──────────────────────────────────
async function refreshProfiles() {
    try {
        state.profiles = await apiCall('GET', '/exposures');
        renderProfiles();
        updateProfileSelectors();
        updateDashboardMetrics();
    } catch (e) {
        console.error('Failed to refresh profiles:', e);
    }
}

function renderProfiles() {
    const list = document.getElementById('profiles-list');
    if (!state.profiles.length) {
        list.innerHTML = '<div class="empty-state"><p>No profiles loaded yet.</p><p class="text-muted">Upload exposures or load the sample dataset.</p></div>';
        return;
    }
    list.innerHTML = state.profiles.map(p => `
        <div class="profile-item">
            <div class="profile-info">
                <h4>${p.company_name}</h4>
                <span>${p.num_exposures} exposures · ${p.base_currency} base · ${new Date(p.created_at).toLocaleTimeString()}</span>
            </div>
            <span class="profile-id">${p.profile_id}</span>
        </div>
    `).join('');
}

function updateProfileSelectors() {
    const selectors = document.querySelectorAll('.profile-select');
    selectors.forEach(sel => {
        const currentVal = sel.value;
        sel.innerHTML = state.profiles.length
            ? state.profiles.map(p => `<option value="${p.profile_id}">${p.company_name} (${p.profile_id})</option>`).join('')
            : '<option value="">No profiles loaded</option>';
        if (currentVal && [...sel.options].find(o => o.value === currentVal)) {
            sel.value = currentVal;
        }
    });
}

async function submitExposures(event) {
    event.preventDefault();
    showLoading();
    try {
        const company = document.getElementById('exp-company').value;
        const baseCurrency = document.getElementById('exp-base-currency').value;
        const expData = JSON.parse(document.getElementById('exp-data').value);

        await apiCall('POST', '/exposures', {
            company_name: company,
            base_currency: baseCurrency,
            exposures: expData,
        });

        showToast(`Profile created for "${company}"`, 'success');
        document.getElementById('exposure-form').reset();
        await refreshProfiles();
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

// ── Scenarios Management ─────────────────────────────────
async function refreshScenarios() {
    try {
        state.scenarios = await apiCall('GET', '/scenarios');
        renderScenarios();
        updateScenarioSelectors();
        updateDashboardMetrics();
    } catch (e) {
        console.error('Failed to refresh scenarios:', e);
    }
}

function renderScenarios() {
    const grid = document.getElementById('scenarios-grid');
    if (!state.scenarios.length) {
        grid.innerHTML = '<div class="empty-state"><p>No scenarios found.</p></div>';
        return;
    }
    grid.innerHTML = state.scenarios.map(s => {
        const shockTags = Object.entries(s.shock_percentages).map(([ccy, shock]) => {
            const pct = (shock * 100).toFixed(1);
            const cls = shock < 0 ? 'negative' : 'positive';
            const sign = shock >= 0 ? '+' : '';
            return `<span class="shock-tag ${cls}">${ccy} ${sign}${pct}%</span>`;
        }).join('');
        const badgeClass = s.created_by === 'system' ? 'system' : 'custom';
        return `
            <div class="scenario-card">
                <div class="scenario-card-header">
                    <span class="scenario-name">${s.name}</span>
                    <span class="scenario-badge ${badgeClass}">${s.created_by}</span>
                </div>
                <div class="scenario-desc">${s.description || 'No description'}</div>
                <div class="scenario-shocks">${shockTags}</div>
            </div>
        `;
    }).join('');
}

function updateScenarioSelectors() {
    const selectors = document.querySelectorAll('.scenario-select');
    selectors.forEach(sel => {
        const currentVal = sel.value;
        let opts = '<option value="">Base Case (no shock)</option>';
        opts += state.scenarios.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
        sel.innerHTML = opts;
        if (currentVal) sel.value = currentVal;
    });
}

function toggleCreateScenario() {
    const panel = document.getElementById('create-scenario-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

async function createScenario(event) {
    event.preventDefault();
    showLoading();
    try {
        const name = document.getElementById('scen-name').value;
        const desc = document.getElementById('scen-desc').value;
        const shocks = JSON.parse(document.getElementById('scen-shocks').value);

        await apiCall('POST', '/scenarios', {
            name, description: desc, shock_percentages: shocks,
        });

        showToast(`Scenario "${name}" created`, 'success');
        document.getElementById('create-scenario-panel').style.display = 'none';
        await refreshScenarios();
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

// ── Dashboard Metrics ────────────────────────────────────
async function updateDashboardMetrics() {
    document.getElementById('metric-profiles').textContent = state.profiles.length;
    document.getElementById('metric-scenarios').textContent = state.scenarios.length;

    if (state.profiles.length > 0) {
        try {
            const profileId = state.profiles[0].profile_id;
            const pnl = await apiCall('POST', '/run_pnl', { profile_id: profileId });
            document.getElementById('metric-profit').textContent = formatCurrency(pnl.profit);
            document.getElementById('metric-profit-sub').textContent = `${state.profiles[0].company_name} · Margin: ${(pnl.margin * 100).toFixed(1)}%`;
        } catch (e) { /* silent */ }
    }
}

// ── P&L Analysis ─────────────────────────────────────────
async function runPnL() {
    const profileId = document.getElementById('pnl-profile').value;
    if (!profileId) { showToast('Select a profile first', 'error'); return; }

    showLoading();
    try {
        const scenarioName = document.getElementById('pnl-scenario').value || undefined;
        const body = { profile_id: profileId };
        if (scenarioName) body.scenario_name = scenarioName;

        const data = await apiCall('POST', '/run_pnl', body);
        renderPnLResults(data);
        showToast('P&L analysis complete', 'success');
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

function renderPnLResults(data) {
    const resultsDiv = document.getElementById('pnl-results');
    const profitClass = data.profit >= 0 ? 'positive' : 'negative';

    resultsDiv.innerHTML = `
        <div class="pnl-result-grid">
            <div class="pnl-item">
                <div class="pnl-item-label">Total Revenue</div>
                <div class="pnl-item-value positive">${formatCurrency(data.total_revenue)}</div>
            </div>
            <div class="pnl-item">
                <div class="pnl-item-label">Total Cost</div>
                <div class="pnl-item-value negative">${formatCurrency(data.total_cost)}</div>
            </div>
            <div class="pnl-item">
                <div class="pnl-item-label">Net Profit</div>
                <div class="pnl-item-value ${profitClass}">${formatCurrency(data.profit)}</div>
            </div>
            <div class="pnl-item">
                <div class="pnl-item-label">Margin</div>
                <div class="pnl-item-value">${(data.margin * 100).toFixed(2)}%</div>
            </div>
        </div>
    `;

    // Breakdown table
    if (data.breakdown && data.breakdown.length) {
        const tbody = document.querySelector('#pnl-breakdown-table tbody');
        tbody.innerHTML = data.breakdown.map(b => `
            <tr>
                <td>${b.name}</td>
                <td class="${b.type === 'revenue' ? 'text-revenue' : 'text-cost'}">${b.type.toUpperCase()}</td>
                <td>${formatNumber(b.original_amount)}</td>
                <td>${b.currency}</td>
                <td>${b.fx_rate.toFixed(4)}</td>
                <td>${formatCurrency(b.amount_in_base)}</td>
            </tr>
        `).join('');
        document.getElementById('pnl-breakdown-card').style.display = 'block';
    }
}

// ── Sensitivity Analysis ─────────────────────────────────
async function runSensitivity() {
    const profileId = document.getElementById('sens-profile').value;
    const currency = document.getElementById('sens-currency').value;
    if (!profileId) { showToast('Select a profile first', 'error'); return; }

    showLoading();
    try {
        const data = await apiCall('POST', '/run_sensitivity', {
            profile_id: profileId,
            target_currency: currency,
        });

        renderSensitivityChart(data);
        showToast('Sensitivity analysis complete', 'success');
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

function renderSensitivityChart(data) {
    // Destroy previous chart
    if (state.charts.sensitivity) state.charts.sensitivity.destroy();

    const ctx = document.getElementById('sensitivity-chart').getContext('2d');
    const labels = data.results.map(r => `${(r.shock_percent * 100).toFixed(0)}%`);
    const profits = data.results.map(r => r.profit);
    const deltas = data.results.map(r => r.delta_profit);

    const gradient = ctx.createLinearGradient(0, 0, 0, 340);
    gradient.addColorStop(0, 'rgba(201, 168, 76, 0.3)');
    gradient.addColorStop(1, 'rgba(201, 168, 76, 0.02)');

    state.charts.sensitivity = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: `Profit Impact (${data.target_currency} shock)`,
                data: profits,
                borderColor: '#C9A84C',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointBackgroundColor: '#C9A84C',
                pointBorderColor: '#0B1929',
                pointBorderWidth: 2,
                pointHoverRadius: 8,
                borderWidth: 2.5,
            }]
        },
        options: chartOptions('Profit (EUR)', `${data.target_currency} Shock (%)`)
    });

    // Summary
    if (data.summary) {
        const sumDiv = document.getElementById('sensitivity-summary');
        sumDiv.style.display = 'grid';
        sumDiv.innerHTML = `
            <div class="summary-item">
                <div class="summary-label">Min Profit</div>
                <div class="summary-value" style="color:var(--danger)">${formatCurrency(data.summary.min_profit)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Max Profit</div>
                <div class="summary-value" style="color:var(--success)">${formatCurrency(data.summary.max_profit)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Profit Range</div>
                <div class="summary-value" style="color:var(--gold)">${formatCurrency(data.summary.profit_range)}</div>
            </div>
        `;
    }
}

// ── Monte Carlo Simulation ───────────────────────────────
async function runMonteCarlo() {
    const profileId = document.getElementById('mc-profile').value;
    if (!profileId) { showToast('Select a profile first', 'error'); return; }

    showLoading();
    try {
        const data = await apiCall('POST', '/run_montecarlo', {
            profile_id: profileId,
            iterations: parseInt(document.getElementById('mc-iterations').value),
            confidence_level: parseFloat(document.getElementById('mc-confidence').value),
            seed: 42,
        });

        state.lastMCResult = data;
        renderMonteCarloResults(data);
        showToast(`Monte Carlo simulation complete — ${data.iterations} iterations`, 'success');

        // Update dashboard VaR
        document.getElementById('metric-var').textContent = formatCurrency(data.risk_metrics.var_95);
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

function renderMonteCarloResults(data) {
    const m = data.risk_metrics;
    document.getElementById('mc-results-area').style.display = 'block';

    // Key metrics
    document.getElementById('mc-mean').textContent = formatCurrency(m.mean_profit);
    document.getElementById('mc-var').textContent = formatCurrency(m.var_95);
    document.getElementById('mc-cvar').textContent = formatCurrency(m.cvar_95);
    document.getElementById('mc-downside').textContent = `${m.downside_probability}%`;

    // Distribution chart
    renderDistributionChart(data);

    // Stats list
    const statsList = document.getElementById('mc-stats-list');
    statsList.innerHTML = [
        ['Base Profit', formatCurrency(m.base_profit)],
        ['Mean Profit', formatCurrency(m.mean_profit)],
        ['Median Profit', formatCurrency(m.median_profit)],
        ['Std Deviation', formatCurrency(m.std_profit)],
        ['Min Profit', formatCurrency(m.min_profit)],
        ['Max Profit', formatCurrency(m.max_profit)],
        ['5th Percentile', formatCurrency(m.p5_profit)],
        ['95th Percentile', formatCurrency(m.p95_profit)],
        ['VaR (95%)', formatCurrency(m.var_95)],
        ['CVaR (95%)', formatCurrency(m.cvar_95)],
        ['Profit at Risk', formatCurrency(m.profit_at_risk)],
        ['Sharpe-like Ratio', m.sharpe_like_ratio.toFixed(4)],
        ['Skewness', m.skewness.toFixed(4)],
        ['Kurtosis', m.kurtosis.toFixed(4)],
        ['Downside Prob.', `${m.downside_probability}%`],
        ['Simulations', m.num_simulations.toLocaleString()],
    ].map(([label, value]) => `
        <div class="stat-row">
            <span class="stat-label">${label}</span>
            <span class="stat-value">${value}</span>
        </div>
    `).join('');
}

function renderDistributionChart(data) {
    if (state.charts.mc) state.charts.mc.destroy();

    const ctx = document.getElementById('mc-chart').getContext('2d');
    const sample = data.distribution_sample || [];
    const m = data.risk_metrics;

    // Build histogram
    const numBins = 30;
    const min = Math.min(...sample);
    const max = Math.max(...sample);
    const binWidth = (max - min) / numBins;
    const bins = Array(numBins).fill(0);
    const binLabels = [];

    for (let i = 0; i < numBins; i++) {
        const binStart = min + i * binWidth;
        binLabels.push(formatNumber(binStart + binWidth / 2));
    }

    sample.forEach(v => {
        let idx = Math.floor((v - min) / binWidth);
        if (idx >= numBins) idx = numBins - 1;
        if (idx < 0) idx = 0;
        bins[idx]++;
    });

    // Color bins: below VaR = red, above = gold
    const varValue = m.var_95;
    const colors = binLabels.map((_, i) => {
        const val = min + (i + 0.5) * binWidth;
        return val <= varValue ? 'rgba(255, 92, 92, 0.6)' : 'rgba(201, 168, 76, 0.5)';
    });
    const borderColors = binLabels.map((_, i) => {
        const val = min + (i + 0.5) * binWidth;
        return val <= varValue ? 'rgba(255, 92, 92, 0.9)' : 'rgba(201, 168, 76, 0.8)';
    });

    state.charts.mc = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Frequency',
                data: bins,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1,
                borderRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#121E30',
                    borderColor: '#C9A84C',
                    borderWidth: 1,
                    titleColor: '#E8ECF1',
                    bodyColor: '#8B9BB4',
                    padding: 12,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: { 
                        color: '#556577', font: { family: 'Inter', size: 10 },
                        maxTicksLimit: 8,
                    },
                    title: { display: true, text: 'Profit (EUR)', color: '#8B9BB4', font: { family: 'Inter', size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: { color: '#556577', font: { family: 'Inter', size: 10 } },
                    title: { display: true, text: 'Frequency', color: '#8B9BB4', font: { family: 'Inter', size: 11 } }
                }
            }
        }
    });
}

// ── Risk Report ──────────────────────────────────────────
async function runFullRiskReport() {
    const profileId = document.getElementById('risk-profile').value;
    if (!profileId) { showToast('Select a profile first', 'error'); return; }

    showLoading();
    try {
        // Run P&L for base case
        const pnl = await apiCall('POST', '/run_pnl', { profile_id: profileId });

        // Run Monte Carlo
        const mc = await apiCall('POST', '/run_montecarlo', {
            profile_id: profileId,
            iterations: 2000,
            seed: 42,
        });

        // Run stress tests against all scenarios
        const stressResults = [];
        for (const scenario of state.scenarios) {
            try {
                const stressed = await apiCall('POST', '/run_pnl', {
                    profile_id: profileId,
                    scenario_name: scenario.name,
                });
                stressResults.push({
                    name: scenario.name,
                    profit: stressed.profit,
                    delta: stressed.profit - pnl.profit,
                    delta_pct: pnl.profit !== 0 ? ((stressed.profit - pnl.profit) / Math.abs(pnl.profit) * 100) : 0,
                });
            } catch (e) { /* skip */ }
        }

        // Sort by impact
        stressResults.sort((a, b) => a.delta - b.delta);

        renderRiskReport(pnl, mc, stressResults);
        showToast('Comprehensive risk report generated', 'success');
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
    hideLoading();
}

function renderRiskReport(pnl, mc, stressResults) {
    const m = mc.risk_metrics;
    document.getElementById('risk-report-area').style.display = 'block';

    // Determine risk level from downside probability
    let riskLevel, riskColor;
    if (m.downside_probability > 20) {
        riskLevel = 'HIGH'; riskColor = 'var(--danger)';
    } else if (m.downside_probability > 8) {
        riskLevel = 'MEDIUM'; riskColor = 'var(--warning)';
    } else {
        riskLevel = 'LOW'; riskColor = 'var(--success)';
    }

    document.getElementById('risk-level').textContent = riskLevel;
    document.getElementById('risk-level').style.color = riskColor;
    document.getElementById('risk-score-text').textContent = `Downside prob: ${m.downside_probability}%`;
    document.getElementById('risk-base-profit').textContent = formatCurrency(pnl.profit);

    if (stressResults.length) {
        document.getElementById('risk-worst').textContent = formatCurrency(stressResults[0].delta);
        document.getElementById('risk-worst').style.color = 'var(--danger)';
        document.getElementById('risk-worst-name').textContent = stressResults[0].name;
        document.getElementById('risk-best').textContent = formatCurrency(stressResults[stressResults.length - 1].delta);
        document.getElementById('risk-best').style.color = 'var(--success)';
        document.getElementById('risk-best-name').textContent = stressResults[stressResults.length - 1].name;
    }

    // Stress chart
    renderStressChart(stressResults);

    // Risk factors
    const factors = [];
    if (m.downside_probability > 10) factors.push(`High downside probability: ${m.downside_probability}% chance of >20% profit drop`);
    if (Math.abs(m.skewness) > 0.5) factors.push(`Distribution skewness: ${m.skewness.toFixed(2)} — ${m.skewness < 0 ? 'left-tailed (more extreme losses)' : 'right-tailed'}`);
    if (m.std_profit > Math.abs(m.mean_profit) * 0.3) factors.push(`High profit volatility: σ = ${formatCurrency(m.std_profit)}`);
    if (m.profit_at_risk > Math.abs(m.base_profit) * 0.2) factors.push(`Significant profit at risk: ${formatCurrency(m.profit_at_risk)} at 95% confidence`);
    if (stressResults.length && Math.abs(stressResults[0].delta_pct) > 15) factors.push(`Worst stress scenario causes ${stressResults[0].delta_pct.toFixed(1)}% profit change`);
    if (m.kurtosis > 1) factors.push(`Heavy-tailed distribution (kurtosis: ${m.kurtosis.toFixed(2)}) — extreme events more likely`);
    if (!factors.length) factors.push('No significant risk factors detected at current configuration');

    document.getElementById('risk-factors-list').innerHTML = factors.map(f =>
        `<div class="risk-factor"><span class="risk-factor-icon">⚠</span> ${f}</div>`
    ).join('');
}

function renderStressChart(stressResults) {
    if (state.charts.stress) state.charts.stress.destroy();

    const ctx = document.getElementById('risk-stress-chart').getContext('2d');
    const labels = stressResults.map(r => r.name);
    const deltas = stressResults.map(r => r.delta);
    const colors = deltas.map(d => d < 0 ? 'rgba(255, 92, 92, 0.7)' : 'rgba(0, 212, 170, 0.7)');
    const borderColors = deltas.map(d => d < 0 ? '#FF5C5C' : '#00D4AA');

    state.charts.stress = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Profit Impact',
                data: deltas,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 4,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#121E30',
                    borderColor: '#C9A84C',
                    borderWidth: 1,
                    titleColor: '#E8ECF1',
                    bodyColor: '#8B9BB4',
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `Impact: ${formatCurrency(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                    ticks: { color: '#556577', font: { family: 'Inter', size: 10 }, callback: v => formatNumber(v) },
                    title: { display: true, text: 'P&L Impact (EUR)', color: '#8B9BB4', font: { family: 'Inter', size: 11 } }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#E8ECF1', font: { family: 'Inter', size: 11, weight: '500' } },
                }
            }
        }
    });
}

// ── Chart Defaults ───────────────────────────────────────
function chartOptions(yLabel, xLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
            legend: {
                labels: { color: '#8B9BB4', font: { family: 'Inter', size: 11 }, boxWidth: 14, padding: 16 }
            },
            tooltip: {
                backgroundColor: '#121E30',
                borderColor: '#C9A84C',
                borderWidth: 1,
                titleColor: '#E8ECF1',
                bodyColor: '#8B9BB4',
                padding: 12,
                titleFont: { family: 'Inter', weight: '600' },
                bodyFont: { family: 'Inter' },
                callbacks: {
                    label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
                }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                ticks: { color: '#556577', font: { family: 'Inter', size: 10 } },
                title: { display: !!xLabel, text: xLabel, color: '#8B9BB4', font: { family: 'Inter', size: 11 } }
            },
            y: {
                grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
                ticks: { color: '#556577', font: { family: 'Inter', size: 10 }, callback: v => formatNumber(v) },
                title: { display: !!yLabel, text: yLabel, color: '#8B9BB4', font: { family: 'Inter', size: 11 } }
            }
        }
    };
}

// ── Formatters ───────────────────────────────────────────
function formatCurrency(value) {
    if (value === null || value === undefined) return '—';
    const abs = Math.abs(value);
    let formatted;
    if (abs >= 1e6) formatted = `€${(value / 1e6).toFixed(2)}M`;
    else if (abs >= 1e3) formatted = `€${(value / 1e3).toFixed(1)}K`;
    else formatted = `€${value.toFixed(2)}`;
    return formatted;
}

function formatNumber(value) {
    if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(0)}K`;
    return value.toFixed(0);
}
