# Quickstart: Lector de Documentos con Voz

**Objetivo**: validar manualmente, de extremo a extremo, que un documento
Markdown en español se puede subir, narrar y reproducir conforme a `spec.md`.
No contiene código de implementación; referencia `data-model.md` y
`contracts/api.md` para el detalle.

## Prerrequisitos

- Python 3.12 instalado; `uv` instalado (ver `research.md` §1).
- Node.js 20 LTS y `npm` instalados.
- Modelo de voz descargado en `backend/models/`:
  - `es_ES-davefx-medium.onnx`
  - `es_ES-davefx-medium.onnx.json`
  (ver constitución sección 2 y `research.md` §2 para procedencia y licencias).
- Sin conexión a Internet requerida a partir de aquí (síntesis 100% local).

## 1. Preparar el backend

```bash
cd backend
uv sync --locked
uv run uvicorn lector_documentos.main:app --reload --port 8000
```

Verificar arranque: `GET http://localhost:8000/api/documents/00000000-0000-0000-0000-000000000000/status` debe responder `404` (no `503`), confirmando que Piper y el modelo cargaron correctamente al iniciar.

## 2. Preparar el frontend

```bash
cd frontend
npm install
npm run dev
```

Abrir la URL servida (por defecto `http://localhost:5173`).

## 3. Escenario de validación — User Story 1 (P1): carga y narración

1. Crear un archivo `prueba.md` en UTF-8 con contenido en español que incluya
   al menos: un encabezado, dos párrafos, una lista, una cita y un enlace.
2. Subirlo desde la interfaz.
3. **Esperado**: la interfaz muestra el nombre `prueba.md` y el estado
   "cargando/procesando"; en menos de 60 s (SC-001) cambia a "listo".
4. Pulsar Play.
5. **Esperado**: se escucha el contenido en el orden del documento, con pausas
   entre bloques, sin pronunciar símbolos Markdown ni la URL del enlace
   (FR-008..FR-010).

## 4. Escenario de validación — User Story 2 (P2): controles de reproducción

1. Con el audio de la prueba anterior listo, pulsar Pausa a mitad de
   reproducción y luego Play de nuevo.
   - **Esperado**: continúa desde la misma posición (FR-022).
2. Pulsar Detener.
   - **Esperado**: la posición vuelve a 0 (FR-023).
3. Cambiar la velocidad a `1,5×` durante la reproducción.
   - **Esperado**: la velocidad cambia sin recargar ni reiniciar la posición
     (FR-025).
4. Arrastrar la línea de tiempo a la mitad del audio.
   - **Esperado**: la reproducción salta a esa posición (FR-026).

## 5. Escenario de validación — User Story 3 (P2): elementos especiales

1. Crear `prueba-elementos.md` con: una imagen con texto alternativo, una
   imagen sin texto alternativo, una tabla de 2x2, un bloque de código, código
   en línea, una URL aislada y una línea separadora (`---`).
2. Subir y reproducir.
3. **Esperado**: se narra el texto alternativo de la primera imagen, nada para
   la segunda imagen, la tabla por filas (encabezados primero), y se omiten
   por completo el bloque de código, el código en línea, la URL aislada y la
   línea separadora (FR-011..FR-013).

## 6. Escenario de validación — User Story 4 (P3): errores

1. Subir un archivo `.txt` → **Esperado**: error `415` con mensaje claro
   (formato incorrecto).
2. Subir un archivo `.md` de más de 5.000.000 bytes → **Esperado**: error
   `413` con mensaje claro de límite de tamaño.
3. Subir un archivo `.md` vacío → **Esperado**: error `422`, "sin contenido
   para narrar".
4. (Si es posible simular) detener el proceso Piper y reintentar una subida
   válida → **Esperado**: error `503` claro, sin reintento automático a otro
   proveedor (FR-019).

## 7. Escenario de validación — cancelación por nueva carga (FR-031a)

1. Subir `prueba.md` (documento largo) y, antes de que termine de procesarse,
   subir inmediatamente `prueba-elementos.md` desde la misma pestaña/sesión.
2. **Esperado**: el estado del primer trabajo pasa a `cancelado` y sus
   temporales se limpian; el segundo documento se procesa con normalidad.

## 8. Verificación de privacidad y limpieza

1. Completar una narración y cerrar la pestaña.
2. Esperar 5 minutos.
3. **Esperado**: los archivos temporales (`ruta_temporal` de `Documento` y de
   `Audio narrado`) ya no existen en el servidor (SC-005); los registros del
   servidor no contienen el contenido del documento (FR-032).

## 9. Prueba de escucha (previa a publicar, no bloquea desarrollo)

Ejecutar la lista de frases definida en `research.md` §8 y registrar el
resultado (oyente, fecha, % de palabras correctamente identificadas) en la
sección correspondiente de `plan.md` antes de publicar, conforme a SC-003 y a
la constitución.
