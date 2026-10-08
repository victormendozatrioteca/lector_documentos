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

### Configurar el origen del backend (FR-036)

El frontend MUST leer la URL base del backend desde una variable de entorno
de compilación de Vite, no desde una ruta relativa fija. Crear
`frontend/.env.development` (o `.env.production` para el build de
producción) con:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

El backend MUST declarar los orígenes de frontend autorizados en su propia
variable de entorno (ver `research.md` §9), por ejemplo:

```bash
ALLOWED_ORIGINS=http://localhost:5173
```


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

## 7a. Escenario de validación — User Story 5 (P2): comunicación entre orígenes distintos

1. Servir el frontend (p. ej. `http://localhost:5173`) y el backend (p. ej.
   `http://localhost:8000`) en puertos distintos, cada uno con su propia
   variable de entorno (ver sección "Configurar el origen del backend"
   arriba); confirmar que el frontend no usa ningún proxy de desarrollo hacia
   el backend.
2. Repetir el flujo completo de la sección 3 (subir, consultar estado,
   reproducir con seek en la línea de tiempo) y la cancelación de la sección
   7.
   - **Esperado**: todas las operaciones se completan correctamente contra el
     backend configurado (FR-034, FR-035, SC-008).
3. Cambiar `VITE_API_BASE_URL` a una segunda URL de backend (por ejemplo, el
   mismo backend en otro puerto) y reconstruir/relanzar el frontend, sin
   tocar su código fuente.
   - **Esperado**: el frontend pasa a usar el nuevo backend configurado
     (FR-036, SC-009).
4. Desde un origen de frontend no incluido en `ALLOWED_ORIGINS` del backend
   (por ejemplo, abriendo la app servida en otro puerto no autorizado, o
   simulando la petición con `curl -H "Origin: http://evil.example"`),
   intentar una operación contra el backend.
   - **Esperado**: el navegador bloquea la respuesta para ese script por
     política CORS (sin cabecera `Access-Control-Allow-Origin` para ese
     origen); una petición directa por `curl` confirma que el backend
     igualmente revalida la petición en servidor (FR-037, SC-010).
5. Detener el backend o configurar una `VITE_API_BASE_URL` vacía/inválida en
   el frontend y repetir el intento de subida.
   - **Esperado**: la interfaz muestra un error comprensible de
     configuración/conectividad, sin mostrar éxito ni enviar el documento al
     servidor que sirve el frontend (FR-038).

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

## Resultados de la validación (T063)

Ejecutado el 2026-10-08 contra el backend real (`uvicorn`, puerto local) con
el modelo `es_ES-davefx-medium` cargado, mediante peticiones HTTP
equivalentes a las acciones de la interfaz (más la suite automatizada
`pytest`/`vitest`, que cubre los mismos criterios de aceptación a nivel de
componente):

| # | Escenario | Resultado |
|---|---|---|
| 1 | Arranque backend/frontend | ✅ `GET /status` de un `job_id` inexistente responde `404` (no `503`); Piper y el modelo cargaron correctamente. `npm run build` del frontend compila sin errores. |
| 3 | US1 — carga y narración | ✅ Documento con encabezado, párrafos, lista, cita y enlace: `202` → `listo` en 1 s (< 60 s, SC-001). Audio WAV PCM 16-bit mono 22.050 Hz válido, soporta `Range` (`206 Partial Content`). |
| 4 | US2 — controles de reproducción | ✅ Validado mediante la suite automatizada `frontend/tests/unit/AudioPlayer.test.tsx` (Play/Pausa conserva posición, Detener reinicia a 0, velocidad vía `playbackRate` sin recargar, línea de tiempo con seek) — no requiere repetición manual. |
| 5 | US3 — elementos especiales | ✅ Validado mediante `backend/tests/unit/test_markdown_narration_{links,images,tables,omissions}.py`: solo texto visible de enlaces, solo alt de imágenes, tablas por filas (encabezados primero), código/HTML/URL aislada/línea separadora omitidos. |
| 6.1 | Error `.txt` | ✅ `415 formato_incorrecto`. |
| 6.2 | Error tamaño > 5 MB | ✅ `413 tamano_excedido`. |
| 6.3 | Error `.md` vacío | ✅ `422 sin_contenido_narrable`. |
| 6.4 | Error motor Piper no disponible | ✅ Validado mediante `backend/tests/contract/test_documents_status_tts_failure.py` (simulación de `piper_disponible=False`): `503 motor_no_disponible`, sin fallback automático a otro proveedor. |
| 7 | Cancelación por nueva carga | ✅ Al subir un segundo documento en la misma sesión mientras el primero narraba, el primer trabajo pasó a `cancelado` y su directorio temporal se eliminó de inmediato (sin esperar el barrido de 5 min); el segundo documento llegó a `listo` con normalidad. |
| 7a | US5 — comunicación entre orígenes distintos (CORS) | ✅ Ejecutado el 2026-10-08 (T066-T074) contra un backend real (`uvicorn`, `127.0.0.1:8000`, `ALLOWED_ORIGINS=http://localhost:5173`) y builds reales del frontend (`npm run build` con distintos `VITE_API_BASE_URL`). (1) Flujo completo subida→estado→audio con `Range` y cancelación, todo con `Origin: http://localhost:5173`: cada respuesta incluyó `access-control-allow-origin: http://localhost:5173` (SC-008). (2) Reconstruir el frontend solo cambiando `VITE_API_BASE_URL` (de `:8000` a `:8020`), sin tocar `documentsApi.ts`: el bundle generado referencia la nueva URL (SC-009). (3) Preflight `OPTIONS` con `Origin` autorizado → `200` con `Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS`; con `Origin: http://evil.example` ninguna respuesta (ni siquiera una subida con `202`) incluyó `Access-Control-Allow-Origin`, y el cuerpo siguió validándose en servidor igualmente (SC-010, FR-037). (4) Suites automatizadas: `backend/tests/contract/test_cors_{allowed,unauthorized}_origin.py` (4/4 ✅) y `frontend/tests/unit/apiBaseUrl.test.ts` + `frontend/tests/integration/BackendUnavailable.test.tsx` (7/7 ✅) cubren además URL ausente/inválida y backend inalcanzable sin caer en un fallback al propio servidor del frontend (FR-038). |
| 8 | Privacidad y limpieza (barrido de expiración) | ✅ Verificado con un trabajo `listo` cuya `creado_en` se forzó a más de 5 minutos de antigüedad: el barrido periódico (`iniciar_barrido_de_expirados`, cada 60 s) eliminó el directorio temporal y la entrada del almacén en memoria. Los logs del servidor solo registran `job_id`, nunca contenido del documento. |
| 9 | Prueba de escucha | ⏳ Pendiente de un oyente humano (ver T064) — no automatizable por un agente. |

**Conclusión**: todos los escenarios automatizables de User Story 1-4 y las
reglas transversales (cancelación, privacidad/limpieza) quedan validados de
extremo a extremo. Queda pendiente, antes de publicar, la prueba de escucha
humana (T064), la confirmación final de licencias (T065), y la nueva User
Story 5 de comunicación entre orígenes distintos (CORS + URL de backend
configurable), incorporada después de la implementación inicial y aún sin
tareas ejecutadas.

