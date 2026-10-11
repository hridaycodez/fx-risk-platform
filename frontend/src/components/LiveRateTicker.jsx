import { useEffect, useMemo } from 'react';
import { useSelector } from 'react-redux';
import './LiveRateTicker.css';

/**
 * Bloomberg-style horizontal scrolling FX rate ticker.
 * Shows: EUR/USD 1.082 ▲ +0.23%  |  EUR/INR 90.42 ▼ -0.11%  |  EUR/CHF 0.962 ▲ +0.05%
 * Updates every 30s via Socket.io rate_update events.
 */
export default function LiveRateTicker() {
  const { current, previous, meta } = useSelector((state) => state.rates);

  const tickerItems = useMemo(() => {
    if (!current || Object.keys(current).length === 0) return [];

    return Object.entries(current).map(([ccy, rate]) => {
      const prevRate = previous?.[ccy] || rate;
      const change = ((rate - prevRate) / prevRate) * 100;
      const isUp = change >= 0;
      const info = meta?.[ccy] || {};

      return {
        pair: `EUR/${ccy}`,
        rate: rate.toFixed(ccy === 'JPY' || ccy === 'INR' ? 2 : 4),
        change: `${isUp ? '+' : ''}${change.toFixed(2)}%`,
        isUp,
        flag: info.flag || '',
        symbol: info.symbol || '',
      };
    });
  }, [current, previous, meta]);

  if (tickerItems.length === 0) {
    return (
      <div className="ticker-bar ticker-loading">
        <span>📡 Connecting to live FX rates...</span>
      </div>
    );
  }

  // Duplicate items for seamless infinite scroll
  const doubled = [...tickerItems, ...tickerItems];

  return (
    <div className="ticker-bar">
      <div className="ticker-track">
        {doubled.map((item, idx) => (
          <div key={idx} className="ticker-item">
            <span className="ticker-flag">{item.flag}</span>
            <span className="ticker-pair">{item.pair}</span>
            <span className="ticker-rate">{item.rate}</span>
            <span className={`ticker-change ${item.isUp ? 'up' : 'down'}`}>
              {item.isUp ? '▲' : '▼'} {item.change}
            </span>
            <span className="ticker-divider">│</span>
          </div>
        ))}
      </div>
    </div>
  );
}
