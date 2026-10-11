const NodeCache = require('node-cache');
const axios = require('axios');

const cache = new NodeCache({ stdTTL: parseInt(process.env.FX_CACHE_TTL_SECONDS) || 30 });

// All 7 supported currencies (base = EUR)
const SUPPORTED_CURRENCIES = ['USD', 'GBP', 'INR', 'AED', 'JPY', 'CHF'];

// Fallback rates in case API is down (EUR as base)
const FALLBACK_RATES = {
  USD: 1.08,
  GBP: 0.856,
  INR: 90.42,
  AED: 3.97,
  JPY: 161.3,
  CHF: 0.962,
};

// Volatility profiles (annualized std dev) — used by Monte Carlo
const VOLATILITY_PROFILES = {
  USD: 0.05,   // 5%
  GBP: 0.07,   // 7%
  INR: 0.045,  // 4.5%
  AED: 0.01,   // 1%  — USD-pegged, very stable
  JPY: 0.03,   // 3%
  CHF: 0.04,   // 4%  — safe haven, low but not negligible
};

// Currency metadata for frontend display
const CURRENCY_META = {
  EUR: { name: 'Euro',          flag: '🇪🇺', symbol: '€', region: 'Eurozone' },
  USD: { name: 'US Dollar',     flag: '🇺🇸', symbol: '$', region: 'United States' },
  GBP: { name: 'British Pound', flag: '🇬🇧', symbol: '£', region: 'United Kingdom' },
  INR: { name: 'Indian Rupee',  flag: '🇮🇳', symbol: '₹', region: 'India' },
  AED: { name: 'UAE Dirham',    flag: '🇦🇪', symbol: 'د.إ', region: 'Dubai / UAE' },
  JPY: { name: 'Japanese Yen',  flag: '🇯🇵', symbol: '¥', region: 'Japan' },
  CHF: { name: 'Swiss Franc',   flag: '🇨🇭', symbol: 'Fr', region: 'Switzerland', safeHaven: true },
};

/**
 * Fetches live FX rates from Frankfurter API (free, no API key).
 * Caches the result for FX_CACHE_TTL_SECONDS to avoid hammering the API.
 * Falls back to hardcoded rates if the API is unreachable.
 * Base currency: EUR
 */
async function getLiveRates() {
  const cacheKey = 'live_rates';
  const cached = cache.get(cacheKey);
  if (cached) {
    return { ...cached, fromCache: true };
  }

  try {
    const symbols = SUPPORTED_CURRENCIES.join(',');
    const url = `${process.env.FX_API_BASE || 'https://api.frankfurter.app'}/latest?base=EUR&to=${symbols}`;
    const response = await axios.get(url, { timeout: 5000 });

    const rates = response.data.rates;
    const result = {
      base: 'EUR',
      rates,
      volatility: VOLATILITY_PROFILES,
      meta: CURRENCY_META,
      fetchedAt: new Date().toISOString(),
      fromCache: false,
    };

    cache.set(cacheKey, result);
    return result;
  } catch (err) {
    console.warn('⚠️  Frankfurter API unreachable. Using fallback rates.', err.message);
    return {
      base: 'EUR',
      rates: FALLBACK_RATES,
      volatility: VOLATILITY_PROFILES,
      meta: CURRENCY_META,
      fetchedAt: new Date().toISOString(),
      fromCache: false,
      isFallback: true,
    };
  }
}

/**
 * Returns historical rate for a currency pair (used by ML training data endpoint)
 * @param {string} base - base currency e.g. 'EUR'
 * @param {string} to   - target currency e.g. 'INR'
 * @param {string} startDate - YYYY-MM-DD
 * @param {string} endDate   - YYYY-MM-DD
 */
async function getHistoricalRates(base, to, startDate, endDate) {
  try {
    const url = `${process.env.FX_API_BASE || 'https://api.frankfurter.app'}/${startDate}..${endDate}?base=${base}&to=${to}`;
    const response = await axios.get(url, { timeout: 10000 });
    return response.data;
  } catch (err) {
    throw new Error(`Historical rates fetch failed: ${err.message}`);
  }
}

module.exports = {
  getLiveRates,
  getHistoricalRates,
  CURRENCY_META,
  VOLATILITY_PROFILES,
  SUPPORTED_CURRENCIES,
};
