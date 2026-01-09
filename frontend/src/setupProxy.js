const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Determine the backend target based on environment
  // Priority: PROXY_TARGET env var > Docker service name > localhost
  const target = process.env.PROXY_TARGET || process.env.REACT_APP_PROXY_TARGET || 'http://api:8000';
  
  console.log(`[Proxy] Configuring proxy to target: ${target}`);

  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target: target,
      changeOrigin: true,
      ws: true, // Enable WebSocket proxying
      logLevel: 'debug',
    })
  );

  // Proxy health check
  app.use(
    '/health',
    createProxyMiddleware({
      target: target,
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
