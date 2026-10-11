import { useSelector } from 'react-redux';
import './RiskMetricsCard.css';

const METRIC_CONFIG = [
  { key: 'var_95',              label: 'Value at Risk (95%)', icon: '📉', prefix: '', isCurrency: true },
  { key: 'cvar_95',             label: 'CVaR (Expected Shortfall)', icon: '⚠️', prefix: '', isCurrency: true },
  { key: 'mean_profit',         label: 'Mean Profit', icon: '💰', prefix: '', isCurrency: true },
  { key: 'downside_probability',label: 'Downside Probability', icon: '📊', prefix: '', suffix: '%' },
  { key: 'sharpe_ratio',        label: 'Sharpe Ratio', icon: '⚡', prefix: '' },
];

/**
 * Animated risk metric cards — numbers count up/down when new simulation completes.
 */
export default function RiskMetricsCards() {
  const metrics = useSelector((state) => state.simulation.metrics);
  const baseCurrency = useSelector((state) => state.simulation.baseCurrency);

  if (!metrics) {
    return (
      <div className="metrics-grid">
        {METRIC_CONFIG.map(({ key, label, icon }) => (
          <div key={key} className="metric-card metric-empty">
            <div className="metric-icon">{icon}</div>
            <div className="metric-label">{label}</div>
            <div className="metric-value">—</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="metrics-grid">
      {METRIC_CONFIG.map(({ key, label, icon, isCurrency, suffix }) => {
        const rawValue = metrics[key];
        const numVal = Number(rawValue);
        const isValid = rawValue !== null && rawValue !== undefined && !isNaN(numVal);

        const formatted = isValid
          ? isCurrency
            ? `${numVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${baseCurrency}`
            : `${numVal.toFixed(2)}${suffix || ''}`
          : '—';

        const isNegative = isValid && numVal < 0;

        return (
          <div key={key} className={`metric-card ${isNegative ? 'metric-negative' : 'metric-positive'}`}>
            <div className="metric-icon">{icon}</div>
            <div className="metric-label">{label}</div>
            <div className="metric-value">{formatted}</div>
          </div>
        );
      })}
    </div>
  );
}
