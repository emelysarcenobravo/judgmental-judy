import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),
    tailwindcss(),
  ],
  server: {
    // Send /api requests to Flask so the login cookie stays on the same origin.
    proxy: {
      '/api': 'http://localhost:5001',
    },
  },
})
