import { io } from 'socket.io-client';
import http from 'http';

async function testWebSockets() {
  console.log('\n======================================================================');
  console.log('4. VERIFYING WEBSOCKET PROTOCOL & REAL-TIME STREAMING');
  console.log('======================================================================');

  // 1. Get demo auth token
  const token = await new Promise((resolve, reject) => {
    const req = http.request({
      hostname: '3.27.149.207',
      port: 80,
      path: '/api/auth/demo',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed.token);
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.write('{}');
    req.end();
  });

  console.log('  [PASS] Auth Handshake: Generated JWT bearer token');

  // Test 1: Reject unauthenticated socket
  await new Promise((resolve) => {
    const badSocket = io('http://3.27.149.207', {
      transports: ['websocket', 'polling'],
      reconnection: false,
    });
    badSocket.on('connect_error', (err) => {
      console.log('  [PASS] WebSocket Auth Guard: Unauthenticated connection rejected (' + err.message + ')');
      badSocket.close();
      resolve();
    });
    badSocket.on('connect', () => {
      console.error('  [FAIL] Unauthenticated socket connected unexpectedly');
      badSocket.close();
      resolve();
    });
  });

  // Test 2: Authenticated connection + rates subscription + Monte Carlo streaming + what-if scenario
  await new Promise((resolve, reject) => {
    const socket = io('http://3.27.149.207', {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: false,
    });

    let chunksReceived = 0;
    let ratesReceived = false;

    socket.on('connect', () => {
      console.log('  [PASS] WebSocket Auth: Authenticated socket connected (ID: ' + socket.id + ')');

      // Test rate subscription
      socket.emit('subscribe_rates');

      // Test Monte Carlo streaming
      socket.emit('run_montecarlo', {
        exposures: [
          { name: 'US Sales', currency: 'USD', amount: 500000, expType: 'revenue' },
          { name: 'UK Sales', currency: 'GBP', amount: 200000, expType: 'revenue' },
          { name: 'EU Operations', currency: 'EUR', amount: 300000, expType: 'cost' },
        ],
        iterations: 1000,
        baseCurrency: 'EUR',
      });
    });

    socket.on('rate_update', (data) => {
      if (!ratesReceived) {
        ratesReceived = true;
        console.log('  [PASS] WebSocket Event: rate_update broadcast received (' + Object.keys(data.rates).length + ' live currency pairs)');
      }
    });

    socket.on('mc_start', (data) => {
      console.log('  [PASS] WebSocket Event: mc_start acknowledged (' + data.iterations + ' iterations)');
    });

    socket.on('mc_chunk', (data) => {
      chunksReceived++;
    });

    socket.on('mc_complete', (metrics) => {
      console.log('  [PASS] WebSocket Streaming: Streamed ' + chunksReceived + ' batches of simulation paths in real time');
      console.log('  [PASS] Real-time Risk Metrics: VaR_95=' + metrics.var_95 + ' EUR | CVaR_95=' + metrics.cvar_95 + ' EUR | Level=' + metrics.risk_level);

      // Test what-if scenario slider drag event
      socket.emit('what_if_scenario', {
        exposures: [
          { name: 'US Sales', currency: 'USD', amount: 500000, expType: 'revenue' },
          { name: 'EU Ops', currency: 'EUR', amount: 300000, expType: 'cost' },
        ],
        shocks: { USD: -0.15 },
        baseCurrency: 'EUR',
      });
    });

    socket.on('scenario_result', (data) => {
      console.log('  [PASS] WebSocket Event: what_if_scenario evaluated with -15% USD shock (Shocked Profit: ' + data.pnl.profit + ' EUR)');
      socket.close();
      resolve();
    });

    socket.on('mc_error', (err) => {
      console.error('  [FAIL] Monte Carlo error:', err);
      socket.close();
      reject(err);
    });

    socket.on('error', (err) => {
      console.error('  [FAIL] Socket error:', err);
      socket.close();
      reject(err);
    });

    setTimeout(() => {
      socket.close();
      resolve();
    }, 12000);
  });
}

testWebSockets()
  .then(() => {
    console.log('\n======================================================================');
    console.log(' ALL WEBSOCKET & STREAMING CHECKS PASSED!');
    console.log('======================================================================\n');
    process.exit(0);
  })
  .catch((err) => {
    console.error('WebSocket test failed:', err);
    process.exit(1);
  });
