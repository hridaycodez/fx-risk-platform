const express = require('express');
const { protect } = require('../middleware/auth.middleware');
const { runPnL, runSensitivity } = require('../services/pythonEngine.service');
const { getLiveRates } = require('../services/fxRates.service');
const SimulationResult = require('../models/SimulationResult.model');

const router = express.Router();

// POST /api/simulation/pnl — run deterministic P&L (saved to DB)
router.post('/pnl', protect, async (req, res, next) => {
  try {
    const { exposures, baseCurrency = 'EUR', portfolioId } = req.body;
    if (!exposures?.length) return res.status(400).json({ error: 'exposures required' });

    const { rates } = await getLiveRates();

    const result = await runPnL({ exposures, fx_rates: rates, base_currency: baseCurrency });

    // Save to MongoDB
    const saved = await SimulationResult.create({
      userId: req.user._id,
      portfolioId,
      type: 'pnl',
      params: { baseCurrency, exposures },
      metrics: {
        meanProfit: result.profit,
        p5Profit: result.profit,
        p95Profit: result.profit,
        ...(result.metrics || {}),
      },
      ratesSnapshot: rates,
    });

    res.json({ simulation: saved, result });
  } catch (err) {
    next(err);
  }
});

// POST /api/simulation/sensitivity — run sensitivity analysis
router.post('/sensitivity', protect, async (req, res, next) => {
  try {
    const { exposures, baseCurrency = 'EUR', targetCurrency, portfolioId } = req.body;
    if (!exposures?.length) return res.status(400).json({ error: 'exposures required' });

    const { rates } = await getLiveRates();
    const result = await runSensitivity({
      exposures,
      fx_rates: rates,
      base_currency: baseCurrency,
      target_currency: targetCurrency,
    });

    res.json(result);
  } catch (err) {
    next(err);
  }
});

// GET /api/simulation/history — all past simulations for this user
router.get('/history', protect, async (req, res, next) => {
  try {
    const { limit = 20, page = 1, type } = req.query;
    const filter = { userId: req.user._id };
    if (type) filter.type = type;

    const results = await SimulationResult.find(filter)
      .sort('-createdAt')
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit));

    const total = await SimulationResult.countDocuments(filter);
    res.json({ total, count: total, page: parseInt(page), results });
  } catch (err) {
    next(err);
  }
});

// GET /api/simulation/history/:id — single past simulation
router.get('/history/:id', protect, async (req, res, next) => {
  try {
    const result = await SimulationResult.findOne({ _id: req.params.id, userId: req.user._id });
    if (!result) return res.status(404).json({ error: 'Simulation not found' });
    res.json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
