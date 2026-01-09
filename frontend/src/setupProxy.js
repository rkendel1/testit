const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Determine the backend target based on environment
  // Priority:
  //   1. PROXY_TARGET - Direct override for special cases
  //   2. REACT_APP_PROXY_TARGET - Standard React env var (used in docker-compose.yml)
  //   3. Default: http://api:8000 - Docker service name for docker-compose
  const target = process.env.PROXY_TARGET || process.env.REACT_APP_PROXY_TARGET || 'http://api:8000';
  
  console.log(`[Proxy] Configuring proxy to target: ${target}`);

  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target,
      changeOrigin: true,
      ws: true, // Enable WebSocket proxying
      logLevel: 'debug',
    })
  );

  // Proxy health check
  app.use(
    '/health',
    createProxyMiddleware({
      target,
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
