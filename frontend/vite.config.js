import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',   // required so the dev server is reachable from outside the container
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true, // required for hot reload to work reliably with Docker volume mounts
    },
  },
})
