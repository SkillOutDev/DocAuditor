import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

function loginRoutePlugin() {
  const rewriteLoginRoute = (req, _res, next) => {
    if (req.method === 'GET' && req.url?.split('?')[0] === '/login') {
      req.url = `/login.html${req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : ''}`;
    }
    next();
  };

  return {
    name: 'login-route',
    configureServer(server) {
      server.middlewares.use(rewriteLoginRoute);
    },
    configurePreviewServer(server) {
      server.middlewares.use(rewriteLoginRoute);
    },
  };
}

export default defineConfig({
  plugins: [loginRoutePlugin(), tailwindcss()],
  appType: 'mpa',
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        login: 'login.html',
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
});
