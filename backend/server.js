require('dotenv').config();
const http = require('http');
const app = require('./src/app');
const { initSocket } = require('./src/socket/simulationSocket');

const PORT = process.env.PORT || 4000;

const server = http.createServer(app);

// Attach Socket.io to the HTTP server
initSocket(server);

server.listen(PORT, () => {
  console.log('╔══════════════════════════════════════╗');
  console.log(`║   FX Risk Platform - Node.js Server  ║`);
  console.log(`║   Running on port ${PORT}               ║`);
  console.log(`║   Environment: ${process.env.NODE_ENV || 'development'}          ║`);
  console.log('╚══════════════════════════════════════╝');
});

// Graceful shutdown
process.on('SIGTERM', () => {
  server.close(() => {
    console.log('Server shut down gracefully.');
    process.exit(0);
  });
});
