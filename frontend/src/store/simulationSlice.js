import { createSlice } from '@reduxjs/toolkit';

const simulationSlice = createSlice({
  name: 'simulation',
  initialState: {
    // Monte Carlo state
    status: 'idle',           // 'idle' | 'running' | 'complete' | 'error'
    progress: 0,              // 0 to 1
    iteration: 0,
    totalIterations: 5000,
    allProfits: [],           // accumulates all streamed profit values
    metrics: null,            // final VaR, CVaR, Sharpe, risk level, etc.
    error: null,

    // What-If scenario state
    shocks: {},               // { USD: 0, GBP: 0, INR: 0, AED: 0, JPY: 0, CHF: 0 }
    scenarioResult: null,     // instant PnL result from slider changes

    // Portfolio state
    exposures: [
      { name: 'US Sales', expType: 'revenue', amount: 500000, currency: 'USD' },
      { name: 'UK Sales', expType: 'revenue', amount: 200000, currency: 'GBP' },
      { name: 'India Ops', expType: 'cost', amount: 15000000, currency: 'INR' },
    ],
    baseCurrency: 'EUR',
  },
  reducers: {
    // Monte Carlo lifecycle
    startSimulation: (state, action) => {
      state.status = 'running';
      state.progress = 0;
      state.iteration = 0;
      state.totalIterations = action.payload?.iterations || 5000;
      state.allProfits = [];
      state.metrics = null;
      state.error = null;
    },
    addChunk: (state, action) => {
      const { profits = [], progress = 0, iteration } = action.payload || {};
      state.allProfits = [...state.allProfits, ...profits];
      state.progress = progress;
      state.iteration =
        typeof iteration === 'number'
          ? iteration
          : progress > 0
            ? Math.round(progress * state.totalIterations)
            : state.allProfits.length;
    },
    completeSimulation: (state, action) => {
      state.status = 'complete';
      state.progress = 1;
      state.iteration = state.totalIterations;
      state.metrics = action.payload;
    },
    failSimulation: (state, action) => {
      state.status = 'error';
      state.error = action.payload;
    },
    resetSimulation: (state) => {
      state.status = 'idle';
      state.progress = 0;
      state.iteration = 0;
      state.allProfits = [];
      state.metrics = null;
      state.error = null;
    },

    // What-If sliders
    setShock: (state, action) => {
      const { currency, value } = action.payload;
      state.shocks[currency] = value;
    },
    setScenarioResult: (state, action) => {
      state.scenarioResult = action.payload;
    },

    // Portfolio
    setExposures: (state, action) => {
      state.exposures = action.payload;
    },
    setBaseCurrency: (state, action) => {
      state.baseCurrency = action.payload;
    },
  },
});

export const {
  startSimulation,
  addChunk,
  completeSimulation,
  failSimulation,
  resetSimulation,
  setShock,
  setScenarioResult,
  setExposures,
  setBaseCurrency,
} = simulationSlice.actions;

export default simulationSlice.reducer;
