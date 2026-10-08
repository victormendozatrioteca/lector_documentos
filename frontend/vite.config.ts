/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/setup.ts',
    env: {
      // Valor por defecto para pruebas que no verifican la resolución de la
      // URL base en sí (FR-034..FR-036); los tests específicos de esa
      // resolución la sobrescriben con `vi.stubEnv`.
      VITE_API_BASE_URL: 'http://localhost:8000',
    },
  },
})
