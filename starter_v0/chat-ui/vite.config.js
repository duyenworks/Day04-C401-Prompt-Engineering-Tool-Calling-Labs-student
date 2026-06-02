import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,
    proxy: {
      '/conversations': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/providers': 'http://localhost:8000',
    },
  },
})
