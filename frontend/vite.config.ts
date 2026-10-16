import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // En desarrollo, /api/orders -> http://localhost:8080/orders (en Docker lo hace nginx).
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (ruta) => ruta.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.test.{ts,tsx}'], // evita que Vitest tome las pruebas de e2e/
  },
});
