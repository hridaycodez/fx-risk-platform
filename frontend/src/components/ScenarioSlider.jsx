import { useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setShock } from '../store/simulationSlice';
import { CURRENCY_META } from '../store/ratesSlice';
import './ScenarioSlider.css';

/**
 * What-If Scenario Sliders — one slider per currency in the user's portfolio.
 * On drag (debounced), emits what_if_scenario Socket.io event.
 * AED has smaller range (±10%) since it's USD-pegged.
 */

const SHOCK_RANGES = {
  USD: { min: -30, max: 30 },
  GBP: { min: -30, max: 30 },
  INR: { min: -20, max: 20 },
  AED: { min: -10, max: 10 },
  JPY: { min: -25, max: 25 },
  CHF: { min: -25, max: 25 },
};

export default function ScenarioSlider({ onScenarioChange }) {
  const dispatch = useDispatch();
  const shocks = useSelector((state) => state.simulation.shocks);
  const exposures = useSelector((state) => state.simulation.exposures);

  // Get unique currencies from exposures
  const currencies = [...new Set(exposures.map((e) => e.currency).filter((c) => c !== 'EUR'))];

  const handleSliderChange = useCallback(
    (currency, value) => {
      const numVal = parseFloat(value) / 100; // convert % to decimal
      dispatch(setShock({ currency, value: numVal }));

      // Debounced callback to parent for Socket.io emission
      if (onScenarioChange) {
        clearTimeout(window._scenarioTimer);
        window._scenarioTimer = setTimeout(() => {
          const currentShocks = { ...shocks, [currency]: numVal };
          onScenarioChange(currentShocks);
        }, 300);
      }
    },
    [dispatch, shocks, onScenarioChange]
  );

  if (currencies.length === 0) {
    return (
      <div className="slider-panel">
        <h3 className="slider-title">📊 What-If Scenarios</h3>
        <p className="slider-empty">Add exposures to enable scenario sliders</p>
      </div>
    );
  }

  return (
    <div className="slider-panel">
      <h3 className="slider-title">📊 What-If Scenarios</h3>
      <p className="slider-subtitle">Drag sliders to see instant impact on P&L</p>

      {currencies.map((ccy) => {
        const range = SHOCK_RANGES[ccy] || { min: -20, max: 20 };
        const meta = CURRENCY_META[ccy] || {};
        const currentVal = (shocks[ccy] || 0) * 100; // decimal to %

        return (
          <div key={ccy} className="slider-row">
            <div className="slider-header">
              <span className="slider-label">
                {meta.flag} {ccy}
              </span>
              <span className={`slider-value ${currentVal > 0 ? 'positive' : currentVal < 0 ? 'negative' : ''}`}>
                {currentVal > 0 ? '+' : ''}{currentVal.toFixed(1)}%
              </span>
            </div>
            <div className="slider-track-container">
              <span className="slider-bound">{range.min}%</span>
              <input
                type="range"
                min={range.min}
                max={range.max}
                step="0.5"
                value={currentVal}
                onChange={(e) => handleSliderChange(ccy, e.target.value)}
                className="slider-input"
              />
              <span className="slider-bound">+{range.max}%</span>
            </div>
          </div>
        );
      })}

      <button
        className="slider-reset-btn"
        onClick={() => {
          currencies.forEach((ccy) => dispatch(setShock({ currency: ccy, value: 0 })));
          if (onScenarioChange) onScenarioChange({});
        }}
      >
        ↺ Reset All
      </button>
    </div>
  );
}
