const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const mongoose = require('mongoose');

// Route imports
const authRoutes = require('./routes/auth.routes');
const ratesRoutes = require('./routes/rates.routes');
const portfolioRoutes = require('./routes/portfolio.routes');
const simulationRoutes = require('./routes/simulation.routes');

const { errorHandler } = require('./middleware/errorHandler');

const app = express();

// ── Security Middleware ──────────────────────────────────────────
app.use(helmet());

const allowedOrigins = [
  'http://localhost:5173',
  'http://localhost:5174',
  process.env.CORS_ORIGIN,
].filter(Boolean);

app.use(cors({
  origin: (origin, callback) => {
    if (
      !origin ||
      origin.startsWith('http://localhost:') ||
      origin.includes('cloudfront.net') ||
      process.env.CORS_ORIGIN === '*' ||
      allowedOrigins.includes(origin)
    ) {
      return callback(null, true);
    }
    return callback(null, true); // Fallback: allow request in production
  },
  credentials: true,
}));

// ── Rate Limiting ────────────────────────────────────────────────
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX) || 100,
  message: { error: 'Too many requests. Please try again later.' },
});
app.use('/api/', limiter);

// ── Body Parsing ─────────────────────────────────────────────────
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true }));

// ── Logging ──────────────────────────────────────────────────────
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('dev'));
}

// ── MongoDB Connection ───────────────────────────────────────────
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('✅ MongoDB connected'))
  .catch((err) => console.error('❌ MongoDB connection error:', err.message));

// ── Health Check ─────────────────────────────────────────────────
const healthHandler = (req, res) => {
  res.json({
    status: 'ok',
    service: 'FX Risk Platform - Node.js Backend',
    timestamp: new Date().toISOString(),
    currencies: process.env.SUPPORTED_CURRENCIES?.split(',') || [],
  });
};
app.get('/health', healthHandler);
app.get('/api/health', healthHandler);

// ── API Routes ───────────────────────────────────────────────────
app.use('/api/auth', authRoutes);
app.use('/api/rates', ratesRoutes);
app.use('/api/portfolio', portfolioRoutes);
app.use('/api/simulation', simulationRoutes);

// ── 404 Handler ──────────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: `Route ${req.originalUrl} not found` });
});

// ── Global Error Handler ─────────────────────────────────────────
app.use(errorHandler);

module.exports = app;
