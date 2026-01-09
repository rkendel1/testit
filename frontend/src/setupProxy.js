const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Determine the backend target based on environment
  // Priority:
  //   1. PROXY_TARGET - Direct override for special cases
  //   2. REACT_APP_PROXY_TARGET - Standard React env var (used in docker-compose.yml)
  //   3. Default: http://localhost:8000 - Works both in Docker and locally
  //
  // Note: When running in Docker Compose, REACT_APP_PROXY_TARGET should be set to http://api:8000
  // When running locally (npm start), it will default to http://localhost:8000
  const target = process.env.PROXY_TARGET || process.env.REACT_APP_PROXY_TARGET || 'http://localhost:8000';
  
  console.log(`[Proxy] Configuring proxy to target: ${target}`);

  // Proxy configuration with error handling
  const proxyConfig = {
    target,
    changeOrigin: true,
    ws: true, // Enable WebSocket proxying
    logLevel: 'debug',
    onError: (err, req, res) => {
      console.error('[Proxy Error]', err.message);
      console.error('[Proxy] Failed to proxy request:', req.url);
      console.error('[Proxy] Target:', target);
      console.error('[Proxy] Suggestion: Ensure backend is running at', target);
      res.writeHead(504, {
        'Content-Type': 'application/json',
      });
      res.end(JSON.stringify({ 
        error: 'Proxy Error',
        message: `Failed to connect to backend at ${target}`,
        details: err.message,
        suggestion: `Make sure the backend API is running at ${target}`
      }));
    }
  };

  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware(proxyConfig)
  );

  // Proxy health check
  app.use(
    '/health',
    createProxyMiddleware(proxyConfig)
  );
};
