import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
      ignored: ['**/entrust/**', '**/backend/**', '**/node_modules/**']
    }
  },
  optimizeDeps: {
    exclude: ['entrust', 'backend']
  }
})