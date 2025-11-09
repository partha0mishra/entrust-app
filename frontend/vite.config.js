import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
      ignored: ['**/entrust/**', '**/enlora/**', '**/llama.cpp/**']
    },
    fs: {
      strict: false,
      deny: ['/app/entrust']
    }
  },
  optimizeDeps: {
    exclude: ['entrust', 'enlora'],
    entries: [
      'src/**/*.{jsx,js,ts,tsx}',
      'index.html'
    ]
  },
  build: {
    rollupOptions: {
      external: [/\/entrust\//, /\/enlora\//]
    }
  }
})