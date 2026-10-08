# Lector de Documentos con Voz — Frontend

Interfaz web (React + TypeScript + Vite + Tailwind) para subir un documento
Markdown en español y escucharlo narrado con audio generado localmente por el
backend (Piper, `es_ES-davefx-medium`).

## Requisitos

- Node.js ≥ 20
- El backend FastAPI corriendo (ver `../backend/README.md`)

## Instalación y desarrollo

```bash
cd frontend
npm install
npm run dev
```

## Configuración de la URL del backend

El frontend y el backend se sirven desde orígenes distintos (sin proxy), tanto
en desarrollo como en producción (FR-034, FR-035). La URL base absoluta del
backend se configura por entorno con `VITE_API_BASE_URL` (variable de
compilación de Vite), sin valores fijos en el código fuente (FR-036):

- `.env.development` (versionado, sin secretos): valor por defecto
  `http://localhost:8000` para desarrollo local.
- `.env.production.example` (versionado, plantilla): cópialo a
  `.env.production` (no se versiona) y ajusta la URL real del backend
  desplegado antes de ejecutar `npm run build`.

Si la variable falta, es inválida, o el backend configurado no responde, la
interfaz muestra un error comprensible sin enviar el documento a ningún otro
servidor (FR-038).


## Comandos de control de calidad

Ejecutar antes de cada commit o pull request:

```bash
npm run test        # Pruebas (vitest)
npm run typecheck   # Tipado estático (tsc --noEmit)
npm run build       # Compilación de producción (tsc -b && vite build)
npm run lint        # ESLint
npm run format:check  # Prettier (sin aplicar cambios)
```

## Notas de privacidad

El documento se envía al backend para generar el audio; no se conserva de
forma permanente ni el documento ni el audio resultante (ver aviso en la
propia interfaz).
