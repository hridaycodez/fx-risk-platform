import { createSlice } from '@reduxjs/toolkit';

const CURRENCY_META = {
  EUR: { name: 'Euro',          flag: '🇪🇺', symbol: '€' },
  USD: { name: 'US Dollar',     flag: '🇺🇸', symbol: '$' },
  GBP: { name: 'British Pound', flag: '🇬🇧', symbol: '£' },
  INR: { name: 'Indian Rupee',  flag: '🇮🇳', symbol: '₹' },
  AED: { name: 'UAE Dirham',    flag: '🇦🇪', symbol: 'د.إ' },
  JPY: { name: 'Japanese Yen',  flag: '🇯🇵', symbol: '¥' },
  CHF: { name: 'Swiss Franc',   flag: '🇨🇭', symbol: 'Fr' },
};

const ratesSlice = createSlice({
  name: 'rates',
  initialState: {
    current: {},          // { USD: 1.08, GBP: 0.856, INR: 90.42, ... }
    previous: {},         // previous rates for delta calculation
    volatility: {},       // { USD: 0.05, GBP: 0.07, ... }
    meta: CURRENCY_META,
    fetchedAt: null,
    fromCache: false,
    isFallback: false,
    loading: false,
    error: null,
  },
  reducers: {
    setRates: (state, action) => {
      state.previous = { ...state.current };
      state.current = action.payload.rates || {};
      state.volatility = action.payload.volatility || state.volatility;
      state.fetchedAt = action.payload.fetchedAt || new Date().toISOString();
      state.fromCache = action.payload.fromCache || false;
      state.isFallback = action.payload.isFallback || false;
      state.loading = false;
      state.error = null;
    },
    setLoading: (state) => {
      state.loading = true;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
    },
  },
});

export const { setRates, setLoading, setError } = ratesSlice.actions;
export { CURRENCY_META };
export default ratesSlice.reducer;
