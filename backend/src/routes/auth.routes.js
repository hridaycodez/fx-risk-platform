const express = require('express');
const { body, validationResult } = require('express-validator');
const jwt = require('jsonwebtoken');
const User = require('../models/User.model');

const router = express.Router();

const signToken = (id, name) =>
  jwt.sign({ id, name }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  });

// POST /api/auth/register
router.post(
  '/register',
  [
    body('name').trim().notEmpty().withMessage('Name is required'),
    body('email').isEmail().withMessage('Valid email required'),
    body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { name, email, password } = req.body;
      const existing = await User.findOne({ email });
      if (existing) {
        return res.status(409).json({ error: 'Email already registered' });
      }

      const user = await User.create({ name, email, password });
      const token = signToken(user._id, user.name);

      res.status(201).json({ token, user: { id: user._id, name: user.name, email: user.email } });
    } catch (err) {
      next(err);
    }
  }
);

// POST /api/auth/login
router.post(
  '/login',
  [
    body('email').isEmail().withMessage('Valid email required'),
    body('password').notEmpty().withMessage('Password is required'),
  ],
  async (req, res, next) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }

      const { email, password } = req.body;
      const user = await User.findOne({ email }).select('+password');
      if (!user || !(await user.correctPassword(password))) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }

      const token = signToken(user._id, user.name);
      res.json({ token, user: { id: user._id, name: user.name, email: user.email } });
    } catch (err) {
      next(err);
    }
  }
);

// POST /api/auth/demo — instant demo login, no password needed
router.post('/demo', async (req, res, next) => {
  try {
    let demo = await User.findOne({ isDemo: true });
    if (!demo) {
      demo = await User.create({
        name: 'Demo User',
        email: 'demo@fxrisk.app',
        password: 'demo_secure_123',
        isDemo: true,
      });
    }
    const token = signToken(demo._id, demo.name);
    res.json({ token, user: { id: demo._id, name: demo.name, email: demo.email, isDemo: true } });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
