import { configureStore } from '@reduxjs/toolkit';
import ratesReducer from './ratesSlice';
import simulationReducer from './simulationSlice';

export const store = configureStore({
  reducer: {
    rates: ratesReducer,
    simulation: simulationReducer,
  },
});
