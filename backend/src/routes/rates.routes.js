const express = require('express');
const { getLiveRates, getHistoricalRates, CURRENCY_META } = require('../services/fxRates.service');
const { protect } = require('../middleware/auth.middleware');

const router = express.Router();

// GET /api/rates/live — returns current EUR-based rates for all 7 currencies
router.get('/live', protect, async (req, res, next) => {
  try {
    const data = await getLiveRates();
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// GET /api/rates/meta — returns currency metadata (flags, symbols, names)
router.get('/meta', (req, res) => {
  res.json({ currencies: CURRENCY_META });
});

// GET /api/rates/historical?base=EUR&to=INR&from=2024-01-01&to_date=2024-12-31
router.get('/historical', protect, async (req, res, next) => {
  try {
    const { base = 'EUR', to, from, to_date } = req.query;
    if (!to || !from || !to_date) {
      return res.status(400).json({ error: 'Query params required: to, from, to_date' });
    }
    const data = await getHistoricalRates(base, to, from, to_date);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
