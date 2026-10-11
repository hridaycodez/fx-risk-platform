import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setExposures, setBaseCurrency } from '../store/simulationSlice';
import { CURRENCY_META } from '../store/ratesSlice';
import './ExposureForm.css';

const CURRENCIES = ['EUR', 'USD', 'GBP', 'INR', 'AED', 'JPY', 'CHF'];

const EMPTY_EXPOSURE = { name: '', expType: 'revenue', amount: '', currency: 'USD' };

/**
 * Exposure input form — lets users build their FX portfolio.
 * Select base currency, add multiple revenue/cost exposures with currencies and amounts.
 */
export default function ExposureForm({ onSave }) {
  const dispatch = useDispatch();
  const reduxExposures = useSelector((state) => state.simulation.exposures);
  const baseCurrency = useSelector((state) => state.simulation.baseCurrency);
  const rates = useSelector((state) => state.rates.current);

  const [rows, setRows] = useState(
    reduxExposures && reduxExposures.length > 0
      ? reduxExposures
      : [
          { name: 'US Sales', expType: 'revenue', amount: 500000, currency: 'USD' },
          { name: 'UK Sales', expType: 'revenue', amount: 200000, currency: 'GBP' },
          { name: 'India Ops', expType: 'cost', amount: 15000000, currency: 'INR' },
        ]
  );

  const [savedFeedback, setSavedFeedback] = useState(false);

  const syncToRedux = (currentRows) => {
    const validRows = currentRows.filter(
      (r) => r.name && Number(r.amount) > 0 && r.currency
    );
    if (validRows.length > 0) {
      dispatch(setExposures(validRows));
    }
  };

  const handleRowChange = (index, field, value) => {
    const updated = [...rows];
    updated[index] = {
      ...updated[index],
      [field]: field === 'amount' ? (value === '' ? '' : Number(value)) : value,
    };
    setRows(updated);
    syncToRedux(updated);
  };

  const addRow = () => {
    const updated = [...rows, { ...EMPTY_EXPOSURE }];
    setRows(updated);
  };

  const removeRow = (index) => {
    if (rows.length <= 1) return;
    const updated = rows.filter((_, i) => i !== index);
    setRows(updated);
    syncToRedux(updated);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validRows = rows.filter((r) => r.name && Number(r.amount) > 0 && r.currency);
    dispatch(setExposures(validRows));
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 2000);
    if (onSave) onSave(validRows);
  };

  const getConvertedValue = (amount, currency) => {
    if (!rates || !amount || currency === baseCurrency) return amount || 0;
    const rate = rates[currency];
    if (!rate) return amount;
    return (amount / rate).toFixed(2);
  };

  return (
    <form className="exposure-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h3>💼 Portfolio Exposures</h3>
        <div className="base-currency-select">
          <label>Base Currency:</label>
          <select
            value={baseCurrency}
            onChange={(e) => dispatch(setBaseCurrency(e.target.value))}
          >
            {CURRENCIES.map((ccy) => (
              <option key={ccy} value={ccy}>
                {CURRENCY_META[ccy]?.flag} {ccy} — {CURRENCY_META[ccy]?.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="exposure-rows">
        {rows.map((row, idx) => (
          <div key={idx} className="exposure-row">
            <input
              type="text"
              placeholder="Exposure name"
              value={row.name}
              onChange={(e) => handleRowChange(idx, 'name', e.target.value)}
              className="exp-input exp-name"
              required
            />
            <select
              value={row.expType}
              onChange={(e) => handleRowChange(idx, 'expType', e.target.value)}
              className="exp-input exp-type"
            >
              <option value="revenue">💚 Revenue</option>
              <option value="cost">🔴 Cost</option>
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={row.amount}
              onChange={(e) => handleRowChange(idx, 'amount', e.target.value)}
              className="exp-input exp-amount"
              min="0"
              required
            />
            <select
              value={row.currency}
              onChange={(e) => handleRowChange(idx, 'currency', e.target.value)}
              className="exp-input exp-currency"
            >
              {CURRENCIES.map((ccy) => (
                <option key={ccy} value={ccy}>
                  {CURRENCY_META[ccy]?.flag} {ccy}
                </option>
              ))}
            </select>
            <span className="exp-converted">
              ≈ {getConvertedValue(row.amount, row.currency)} {baseCurrency}
            </span>
            <button
              type="button"
              className="exp-remove-btn"
              onClick={() => removeRow(idx)}
              disabled={rows.length <= 1}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="form-actions">
        <button type="button" className="add-row-btn" onClick={addRow}>
          + Add Exposure
        </button>
        <button
          type="submit"
          className="save-btn"
          style={{ backgroundColor: savedFeedback ? '#238636' : undefined }}
        >
          {savedFeedback ? '✓ Portfolio Updated!' : '✓ Set Portfolio'}
        </button>
      </div>
    </form>
  );
}
