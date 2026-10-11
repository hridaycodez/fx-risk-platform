const { Server } = require('socket.io');
const jwt = require('jsonwebtoken');
const { getLiveRates } = require('../services/fxRates.service');
const { streamMonteCarlo, runPnL } = require('../services/pythonEngine.service');

let io;
let ratesBroadcastInterval = null;

/**
 * Initialise Socket.io and attach all event handlers.
 * @param {http.Server} server
 */
function initSocket(server) {
  io = new Server(server, {
    cors: {
      origin: (origin, callback) => {
        if (
          !origin ||
          origin.startsWith('http://localhost:') ||
          origin.includes('cloudfront.net') ||
          process.env.CORS_ORIGIN === '*' ||
          origin === process.env.CORS_ORIGIN
        ) {
          return callback(null, true);
        }
        callback(null, false);
      },
      methods: ['GET', 'POST'],
      credentials: true,
    },
  });

  // ── JWT Auth Middleware ─────────────────────────────────────────
  io.use((socket, next) => {
    const token = socket.handshake.auth?.token;
    if (!token) return next(new Error('Authentication required'));
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.userId = decoded.id;
      socket.userName = decoded.name;
      next();
    } catch {
      next(new Error('Invalid or expired token'));
    }
  });

  io.on('connection', (socket) => {
    console.log(`🔌 Socket connected: ${socket.id} (user: ${socket.userName})`);

    // ── Event: subscribe_rates ───────────────────────────────────
    // Client wants to receive live FX rate updates every 30s
    socket.on('subscribe_rates', async () => {
      // Immediately send current rates
      try {
        const ratesData = await getLiveRates();
        socket.emit('rate_update', ratesData);
      } catch (err) {
        socket.emit('rate_error', { message: 'Failed to fetch live rates' });
      }

      // Join the rates room so global broadcast reaches this client
      socket.join('rates_room');
    });

    socket.on('unsubscribe_rates', () => {
      socket.leave('rates_room');
    });

    // ── Event: run_montecarlo ────────────────────────────────────
    // Client starts a live Monte Carlo simulation — results streamed back chunk by chunk
    socket.on('run_montecarlo', async (payload) => {
      const { exposures, iterations = 5000, seed, baseCurrency = 'EUR' } = payload;

      if (!exposures || !Array.isArray(exposures) || exposures.length === 0) {
        return socket.emit('mc_error', { message: 'No exposures provided' });
      }

      try {
        // Fetch live rates to use as the simulation base
        const { rates, volatility } = await getLiveRates();

        const enginePayload = {
          exposures,
          iterations,
          seed,
          base_currency: baseCurrency,
          fx_rates: rates,
          fx_volatility: volatility,
        };

        socket.emit('mc_start', { iterations, message: 'Simulation started...' });

        await streamMonteCarlo(
          enginePayload,
          // onChunk — called ~20 times during a run
          (profits, progress, iteration) => {
            const currentIteration = iteration || (progress ? Math.round(progress * iterations) : 0);
            socket.emit('mc_chunk', {
              profits,
              progress,
              iteration: currentIteration,
            });
          },
          // onComplete — called once with final risk metrics
          (metrics) => {
            socket.emit('mc_complete', metrics);
          }
        );
      } catch (err) {
        console.error('Monte Carlo error:', err.message);
        socket.emit('mc_error', { message: err.message });
      }
    });

    // ── Event: what_if_scenario ──────────────────────────────────
    // Client dragged a slider — recalculate P&L instantly with shocked rates
    socket.on('what_if_scenario', async (payload) => {
      const { exposures, shocks, baseCurrency = 'EUR' } = payload;
      // shocks = { USD: -0.10, INR: 0.05 } means USD -10%, INR +5%

      try {
        const { rates } = await getLiveRates();

        // Apply shocks to live rates
        const shockedRates = { ...rates };
        for (const [currency, shock] of Object.entries(shocks || {})) {
          if (shockedRates[currency] !== undefined) {
            shockedRates[currency] = shockedRates[currency] * (1 + shock);
          }
        }

        const result = await runPnL({
          exposures,
          fx_rates: shockedRates,
          base_currency: baseCurrency,
        });

        socket.emit('scenario_result', {
          shocks,
          shockedRates,
          pnl: result,
        });
      } catch (err) {
        socket.emit('scenario_error', { message: err.message });
      }
    });

    // ── Disconnect ───────────────────────────────────────────────
    socket.on('disconnect', () => {
      console.log(`🔌 Socket disconnected: ${socket.id}`);
    });
  });

  // ── Global Rates Broadcast (every 30s) ──────────────────────────
  // Broadcasts latest rates to ALL subscribed clients at once
  ratesBroadcastInterval = setInterval(async () => {
    try {
      const ratesData = await getLiveRates();
      io.to('rates_room').emit('rate_update', ratesData);
    } catch (err) {
      console.error('Rates broadcast error:', err.message);
    }
  }, 30000);

  console.log('✅ Socket.io initialized');
}

function getIO() {
  if (!io) throw new Error('Socket.io not initialized. Call initSocket() first.');
  return io;
}

module.exports = { initSocket, getIO };
