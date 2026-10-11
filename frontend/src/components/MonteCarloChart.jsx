import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import Plot from 'react-plotly.js';

const formatNum = (val) => {
  if (val === null || val === undefined || isNaN(Number(val))) return '—';
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

/**
 * MonteCarloChart — The showpiece component.
 * Animates a histogram as streaming mc_chunk events arrive.
 * Shows VaR/CVaR lines when simulation completes.
 */
export default function MonteCarloChart() {
  const { allProfits = [], status = 'idle', progress = 0, iteration = 0, totalIterations = 5000, metrics } =
    useSelector((state) => state.simulation || {});
  const baseCurrency = useSelector((state) => state.simulation?.baseCurrency || 'EUR');

  const chartData = useMemo(() => {
    if (!allProfits || allProfits.length === 0) return [];
    return [
      {
        x: allProfits,
        type: 'histogram',
        nbinsx: 60,
        marker: {
          color: 'rgba(56, 189, 248, 0.65)',
          line: { color: 'rgba(56, 189, 248, 0.9)', width: 1 },
        },
        opacity: 0.8,
        name: 'Profit Distribution',
      },
    ];
  }, [allProfits]);

  const shapes = useMemo(() => {
    if (!metrics) return [];
    const lines = [];

    // VaR line (red)
    if (metrics.var_95 != null && !isNaN(metrics.var_95)) {
      lines.push({
        type: 'line',
        x0: metrics.var_95, x1: metrics.var_95,
        y0: 0, y1: 1, yref: 'paper',
        line: { color: '#f85149', width: 2.5, dash: 'dash' },
      });
    }
    // CVaR line (orange)
    if (metrics.cvar_95 != null && !isNaN(metrics.cvar_95)) {
      lines.push({
        type: 'line',
        x0: metrics.cvar_95, x1: metrics.cvar_95,
        y0: 0, y1: 1, yref: 'paper',
        line: { color: '#f0883e', width: 2, dash: 'dot' },
      });
    }
    // Mean profit line (green)
    if (metrics.mean_profit != null && !isNaN(metrics.mean_profit)) {
      lines.push({
        type: 'line',
        x0: metrics.mean_profit, x1: metrics.mean_profit,
        y0: 0, y1: 1, yref: 'paper',
        line: { color: '#3fb950', width: 2.5, dash: 'solid' },
      });
    }

    return lines;
  }, [metrics]);

  const annotations = useMemo(() => {
    if (!metrics) return [];
    const list = [];

    if (metrics.var_95 != null && !isNaN(metrics.var_95)) {
      list.push({
        x: metrics.var_95, y: 0.92, yref: 'paper', xanchor: 'left',
        text: ` VaR 95%: ${formatNum(metrics.var_95)} ${baseCurrency} `,
        font: { color: '#f85149', size: 11, family: 'Inter, sans-serif' },
        bgcolor: 'rgba(13, 17, 23, 0.85)',
        bordercolor: '#f85149',
        borderwidth: 1,
        borderpad: 3,
        showarrow: false,
      });
    }

    if (metrics.cvar_95 != null && !isNaN(metrics.cvar_95)) {
      list.push({
        x: metrics.cvar_95, y: 0.82, yref: 'paper', xanchor: 'right',
        text: ` CVaR: ${formatNum(metrics.cvar_95)} ${baseCurrency} `,
        font: { color: '#f0883e', size: 11, family: 'Inter, sans-serif' },
        bgcolor: 'rgba(13, 17, 23, 0.85)',
        bordercolor: '#f0883e',
        borderwidth: 1,
        borderpad: 3,
        showarrow: false,
      });
    }

    if (metrics.mean_profit != null && !isNaN(metrics.mean_profit)) {
      list.push({
        x: metrics.mean_profit, y: 1.0, yref: 'paper', xanchor: 'left',
        text: ` Mean: ${formatNum(metrics.mean_profit)} ${baseCurrency} `,
        font: { color: '#3fb950', size: 11, family: 'Inter, sans-serif' },
        bgcolor: 'rgba(13, 17, 23, 0.85)',
        bordercolor: '#3fb950',
        borderwidth: 1,
        borderpad: 3,
        showarrow: false,
      });
    }

    return list;
  }, [metrics, baseCurrency]);

  const currentIter = Number(iteration ?? allProfits.length ?? 0);
  const totalIter = Number(totalIterations ?? 5000);

  const titleText =
    status === 'running'
      ? `Monte Carlo Simulation — ${currentIter.toLocaleString()} / ${totalIter.toLocaleString()} iterations`
      : status === 'complete'
        ? `Monte Carlo Simulation — ${totalIter.toLocaleString()} iterations complete`
        : 'Monte Carlo Profit Distribution';

  return (
    <div className="chart-container">
      {/* Progress bar */}
      {status === 'running' && (
        <div className="mc-progress-bar">
          <div
            className="mc-progress-fill"
            style={{ width: `${(Math.min(Math.max(progress, 0), 1) * 100).toFixed(1)}%` }}
          />
          <span className="mc-progress-label">
            {(Math.min(Math.max(progress, 0), 1) * 100).toFixed(0)}%
          </span>
        </div>
      )}

      <Plot
        data={chartData}
        layout={{
          title: {
            text: titleText,
            font: { color: '#c9d1d9', size: 16, family: 'Inter, sans-serif' },
          },
          paper_bgcolor: '#0d1117',
          plot_bgcolor: '#161b22',
          font: { color: '#8b949e' },
          xaxis: {
            title: `Profit (${baseCurrency})`,
            gridcolor: '#21262d',
            zerolinecolor: '#30363d',
          },
          yaxis: {
            title: 'Frequency',
            gridcolor: '#21262d',
            zerolinecolor: '#30363d',
          },
          shapes,
          annotations,
          margin: { t: 50, r: 30, b: 50, l: 60 },
          bargap: 0.02,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%', height: '420px' }}
        useResizeHandler
      />

      {/* ML Risk Badge */}
      {metrics?.risk_level && (
        <div className={`risk-badge risk-${String(metrics.risk_level).toLowerCase()}`}>
          {metrics.risk_level === 'HIGH' && '🔴'}
          {metrics.risk_level === 'MEDIUM' && '🟡'}
          {metrics.risk_level === 'LOW' && '🟢'}
          {' '}{metrics.risk_level} RISK
        </div>
      )}
    </div>
  );
}
