let chartInstance = null;
let importanceChartInstance = null;
let baselineForecast = null;
let debounceTimer = null;

const API_BASE_URL = 'http://localhost:8000';

async function runForecast(isSimulation = false) {
  const raw = document.getElementById('histData').value.trim();
  const data = raw.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
  
  if (data.length < 10) return;

  const payload = {
    store_id: 1,
    sku_id: 1,
    history: data,
    horizon: parseInt(document.getElementById('horizon').value),
    price_override: isSimulation ? parseFloat(document.getElementById('priceOverride').value) : null,
    promo_override: isSimulation ? document.getElementById('promoOverride').checked : null,
    cost_price: parseFloat(document.getElementById('costPrice').value)
  };

  try {
    const response = await fetch(`${API_BASE_URL}/forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Failed to fetch forecast');

    const result = await response.json();
    if (!isSimulation) baselineForecast = result.forecast;
    
    updateUI(data, result, payload.horizon, isSimulation);
    calculateInventoryMetrics(result.forecast);
    
  } catch (error) {
    console.error('Forecast Error:', error);
  }
}

function updateUI(history, result, horizon, isSimulation) {
  const { forecast, confidence_upper, confidence_lower, rmse, r2, feature_importance, projected_revenue, projected_profit } = result;

  // Update Financial Metrics
  document.getElementById('profit-val').textContent = '$' + projected_profit.toLocaleString(undefined, {maximumFractionDigits: 0});
  document.getElementById('revenue-val').textContent = '$' + projected_revenue.toLocaleString(undefined, {maximumFractionDigits: 0});
  
  const margin = (projected_profit / projected_revenue * 100).toFixed(1);
  document.getElementById('margin-badge').textContent = margin + '% Margin';
  document.getElementById('margin-badge').style.borderColor = margin > 20 ? '#10b981' : '#f59e0b';

  document.getElementById('rmse-val').textContent = rmse.toFixed(1);
  document.getElementById('r2-val').textContent = r2.toFixed(4);

  renderMainChart(history, forecast, confidence_upper, confidence_lower, horizon, isSimulation);

  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = '';
  forecast.forEach((val, i) => {
    const baselineVal = baselineForecast ? baselineForecast[i] : val;
    const diff = ((val - baselineVal) / baselineVal * 100).toFixed(1);
    const isPeak = val > (history.reduce((a, b) => a + b, 0) / history.length) * 1.3;
    
    tbody.innerHTML += `
      <tr>
        <td>Week +${i + 1}</td>
        <td><strong>${val.toFixed(0)}</strong></td>
        <td><span style="color: ${diff > 0 ? '#10b981' : '#ef4444'}">${baselineForecast ? (diff > 0 ? '+' : '') + diff + '%' : '--'}</span></td>
        <td><span class="badge" style="border-color: ${isPeak ? '#ef4444' : '#10b981'}; color: ${isPeak ? '#ef4444' : '#10b981'}">${isPeak ? 'PEAK' : 'NORMAL'}</span></td>
      </tr>
    `;
  });

  renderImportanceChart(feature_importance);
}

function renderMainChart(history, forecast, upper, lower, horizon, isSimulation) {
  const labels = [
    ...history.map((_, i) => `W-${history.length - i}`), 
    ...Array.from({ length: horizon }, (_, i) => `F+${i + 1}`)
  ];
  
  if (chartInstance) chartInstance.destroy();
  const ctx = document.getElementById('forecastChart').getContext('2d');
  
  const datasets = [
    { 
      label: 'History', 
      data: [...history, ...new Array(horizon).fill(null)], 
      borderColor: 'rgba(148, 163, 184, 0.5)', 
      borderDash: [5, 5],
      pointRadius: 0,
      fill: false, 
      tension: 0.3 
    },
    { 
      label: 'Forecast', 
      data: [...new Array(history.length).fill(null), ...forecast], 
      borderColor: isSimulation ? '#10b981' : '#6366f1', 
      borderWidth: 3, 
      pointRadius: 0,
      fill: false,
      tension: 0.3,
      zIndex: 10
    }
  ];

  // Add Confidence Interval Shading
  if (upper && lower) {
      datasets.push({
          label: 'Uncertainty Bound',
          data: [...new Array(history.length).fill(null), ...upper],
          borderColor: 'transparent',
          backgroundColor: isSimulation ? 'rgba(16, 185, 129, 0.05)' : 'rgba(99, 102, 241, 0.05)',
          fill: '+1', // Fill to next dataset
          pointRadius: 0,
          tension: 0.3
      });
      datasets.push({
          label: 'Lower Bound',
          data: [...new Array(history.length).fill(null), ...lower],
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
          tension: 0.3
      });
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { 
        legend: { 
            position: 'top', 
            labels: { color: '#94a3b8', font: { size: 10 }, usePointStyle: true, filter: (item) => !item.text.includes('Bound') } 
        } 
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } }
      }
    }
  });
}

function calculateInventoryMetrics(forecast) {
  const avgDemand = forecast.reduce((a, b) => a + b, 0) / forecast.length;
  const stdDev = Math.sqrt(forecast.map(x => Math.pow(x - avgDemand, 2)).reduce((a, b) => a + b) / forecast.length);
  const safetyStock = 1.65 * stdDev * Math.sqrt(2);
  const reorderPoint = (avgDemand * 2) + safetyStock;

  document.getElementById('safety-stock').textContent = safetyStock.toFixed(0);
  document.getElementById('reorder-point').textContent = reorderPoint.toFixed(0);
}

function renderImportanceChart(importance) {
  const sorted = Object.entries(importance).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 5);
  if (importanceChartInstance) importanceChartInstance.destroy();
  const ctx2 = document.getElementById('importanceChart').getContext('2d');
  importanceChartInstance = new Chart(ctx2, {
    type: 'bar',
    data: { labels: sorted.map(s => s.name), datasets: [{ data: sorted.map(s => s.value), backgroundColor: 'rgba(99, 102, 241, 0.8)', borderRadius: 4 }] },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { display: false }, y: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } } }
    }
  });
}

function handleSliderInput(val) {
  document.getElementById('priceVal').textContent = '$' + val;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => runForecast(true), 150);
}

function handleCostInput(val) {
  document.getElementById('costVal').textContent = '$' + val;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => runForecast(true), 150);
}

function handleFileUpload(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const values = e.target.result.split(/[\n,]/).map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
    if (values.length > 0) { document.getElementById('histData').value = values.join(', '); runForecast(false); }
  };
  reader.readAsText(file);
}

window.onload = () => {
    document.getElementById('histData').value = [120,135,142,128,155,167,173,180,192,185,198,210,205,220,215,230,225,240,250,260,255,270,280,290,285,300,310,320,315,330].join(', ');
    runForecast(false);
};
