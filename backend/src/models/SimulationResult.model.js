const mongoose = require('mongoose');

const simulationResultSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    portfolioId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Portfolio',
    },
    type: {
      type: String,
      enum: ['montecarlo', 'pnl', 'sensitivity'],
      required: true,
    },
    params: {
      baseCurrency: String,
      iterations: Number,
      seed: Number,
      exposures: Array,
    },
    metrics: {
      meanProfit: Number,
      var95: Number,      // Value at Risk at 95% confidence
      cvar95: Number,     // Conditional VaR (Expected Shortfall)
      p5Profit: Number,
      p95Profit: Number,
      downsideProbability: Number,
      sharpeRatio: Number,
      volatility: Number,
      riskLevel: {
        type: String,
        enum: ['LOW', 'MEDIUM', 'HIGH'],
      },
    },
    // Snapshot of rates used at time of simulation
    ratesSnapshot: {
      type: Map,
      of: Number,
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model('SimulationResult', simulationResultSchema);
