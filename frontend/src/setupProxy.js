const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://api:8000',
      changeOrigin: true,
      ws: true, // Enable WebSocket proxying
      logLevel: 'debug',
    })
  );

  // Proxy health check
  app.use(
    '/health',
    createProxyMiddleware({
      target: 'http://api:8000',
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
