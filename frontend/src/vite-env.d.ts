/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base absoluta del backend (FR-034, FR-035, FR-036), p. ej.
   * `https://api.midominio.com`. Configurada por entorno en tiempo de
   * compilación; ver `frontend/.env.development` / `.env.production.example`. */
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
