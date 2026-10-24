import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

function loginRoutePlugin() {
  const rewriteLoginRoute = (req, _res, next) => {
    const routes = {
      '/login': '/login.html',
      '/register': '/register.html',
      '/documents': '/documents.html',
    };
    const route = req.url?.split('?')[0];
    if (req.method === 'GET' && route in routes) {
      req.url = `${routes[route]}${req.url.includes('?') ? req.url.slice(req.url.indexOf('?')) : ''}`;
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

const apiProxy = {
  '/api': 'http://127.0.0.1:8000',
};

export default defineConfig({
  plugins: [loginRoutePlugin(), tailwindcss()],
  appType: 'mpa',
  build: {
    rollupOptions: {
      input: {
        main: 'index.html',
        login: 'login.html',
        register: 'register.html',
        documents: 'documents.html',
      },
    },
  },
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
});
