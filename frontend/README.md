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
