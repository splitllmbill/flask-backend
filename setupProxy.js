// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  app.use(
    '/db',
    createProxyMiddleware({
      target: 'https://flask-backend-puce.vercel.app',
      changeOrigin: true,
    })
  );
};
