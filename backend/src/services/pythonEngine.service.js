const axios = require('axios');

const ML_ENGINE_URL = process.env.ML_ENGINE_URL || 'http://localhost:8000';

/**
 * Calls the Python ML Engine to run a full deterministic P&L analysis.
 */
async function runPnL(payload) {
  const response = await axios.post(`${ML_ENGINE_URL}/run_pnl`, payload, { timeout: 15000 });
  return response.data;
}

/**
 * Calls the Python ML Engine to run sensitivity analysis (tornado chart data).
 */
async function runSensitivity(payload) {
  const response = await axios.post(`${ML_ENGINE_URL}/run_sensitivity`, payload, { timeout: 15000 });
  return response.data;
}

/**
 * Calls the Python ML Engine to get ML risk classification and volatility forecast.
 */
async function getMLPrediction(payload) {
  const response = await axios.post(`${ML_ENGINE_URL}/ml/predict`, payload, { timeout: 10000 });
  return response.data;
}

/**
 * Streams Monte Carlo results from Python engine chunk by chunk.
 * Calls the callback `onChunk` with each batch of profits as they arrive.
 * @param {Object} payload - { exposures, iterations, seed, baseCurrency, rates, volatility }
 * @param {Function} onChunk - called with (profits_array, progress_0_to_1)
 * @param {Function} onComplete - called with final risk metrics object
 */
function streamMonteCarlo(payload, onChunk, onComplete) {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await axios.post(
        `${ML_ENGINE_URL}/run_montecarlo_stream`,
        payload,
        {
          responseType: 'stream',
          timeout: 60000,
        }
      );

      let buffer = '';

      response.data.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete last line in buffer

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.type === 'chunk') {
              onChunk(parsed.profits, parsed.progress, parsed.iteration);
            } else if (parsed.type === 'complete') {
              const { type, ...metrics } = parsed;
              onComplete(metrics);
            } else if (parsed.type === 'error') {
              reject(new Error(parsed.message || 'ML engine error in stream'));
            }
          } catch {
            // Ignore malformed lines
          }
        }
      });

      response.data.on('end', () => {
        if (buffer.trim()) {
          try {
            const parsed = JSON.parse(buffer);
            if (parsed.type === 'complete') {
              const { type, ...metrics } = parsed;
              onComplete(metrics);
            }
          } catch { /* ignore */ }
        }
        resolve();
      });

      response.data.on('error', (err) => {
        reject(err);
      });
    } catch (err) {
      reject(new Error(`ML Engine error: ${err.message}`));
    }
  });
}

module.exports = { runPnL, runSensitivity, getMLPrediction, streamMonteCarlo };
