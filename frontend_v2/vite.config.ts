import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  // In dev we proxy /api to the backend so every fetch is same-origin and
  // CORS is sidestepped entirely. In prod VITE_API_URL wins.
  const backendTarget = env.VITE_API_URL || 'http://localhost:8000';
  return {
    server: {
      port: 3001,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
          // Disable proxy timeouts so long-lived SSE/fetch stream requests
          // do not get cut off during optimization.
          timeout: 0,
        },
      },
    },
    plugins: [react(), tailwindcss()],
    define: {
      // During dev, leave VITE_API_URL as an empty string so our fetches
      // resolve to the current origin (and go through the proxy above).
      // Prod builds use whatever VITE_API_URL was set at build time.
      'import.meta.env.VITE_API_URL': JSON.stringify(
        mode === 'development' ? '' : env.VITE_API_URL || 'http://localhost:8000',
      ),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  };
});
