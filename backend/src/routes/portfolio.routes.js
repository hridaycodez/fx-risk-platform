const express = require('express');
const { body, validationResult } = require('express-validator');
const Portfolio = require('../models/Portfolio.model');
const { protect } = require('../middleware/auth.middleware');

const router = express.Router();
const VALID_CURRENCIES = ['EUR', 'USD', 'GBP', 'INR', 'AED', 'JPY', 'CHF'];

// GET /api/portfolio — get all portfolios for logged in user
router.get('/', protect, async (req, res, next) => {
  try {
    const portfolios = await Portfolio.find({ userId: req.user._id }).sort('-createdAt');
    res.json({ count: portfolios.length, portfolios });
  } catch (err) {
    next(err);
  }
});

// GET /api/portfolio/:id — get a single portfolio
router.get('/:id', protect, async (req, res, next) => {
  try {
    const portfolio = await Portfolio.findOne({ _id: req.params.id, userId: req.user._id });
    if (!portfolio) return res.status(404).json({ error: 'Portfolio not found' });
    res.json(portfolio);
  } catch (err) {
    next(err);
  }
});

// POST /api/portfolio — save a new portfolio
router.post(
  '/',
  protect,
  [
    body('name').trim().notEmpty().withMessage('Portfolio name is required'),
    body('baseCurrency').isIn(VALID_CURRENCIES).withMessage('Invalid base currency'),
    body('exposures').isArray({ min: 1 }).withMessage('At least one exposure required'),
    body('exposures.*.name').trim().notEmpty().withMessage('Exposure name required'),
    body('exposures.*.expType').isIn(['revenue', 'cost']).withMessage('expType must be revenue or cost'),
    body('exposures.*.amount').isFloat({ min: 0 }).withMessage('Amount must be a positive number'),
    body('exposures.*.currency').isIn(VALID_CURRENCIES).withMessage('Invalid exposure currency'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

      const { name, baseCurrency, exposures } = req.body;
      const portfolio = await Portfolio.create({
        userId: req.user._id,
        name,
        baseCurrency,
        exposures,
      });

      res.status(201).json(portfolio);
    } catch (err) {
      next(err);
    }
  }
);

// DELETE /api/portfolio/:id
router.delete('/:id', protect, async (req, res, next) => {
  try {
    const portfolio = await Portfolio.findOneAndDelete({ _id: req.params.id, userId: req.user._id });
    if (!portfolio) return res.status(404).json({ error: 'Portfolio not found' });
    res.json({ message: 'Portfolio deleted' });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
