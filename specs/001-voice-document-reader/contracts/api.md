# API Contract: Lector de Documentos con Voz

**Fecha**: 2026-10-08 | **Base path**: `/api`

Este contrato describe la interfaz HTTP expuesta por el backend FastAPI al
frontend. No es una implementación; `/speckit-tasks` debe traducir cada
operación en tareas de implementación y pruebas de contrato.

Todas las respuestas de error usan el cuerpo:

```json
{ "error": { "codigo": "string", "mensaje": "string comprensible para el usuario" } }
```

`mensaje` MUST ser comprensible y MUST NOT incluir trazas, rutas de archivo ni
detalles internos (FR-033). `codigo` es un identificador estable para pruebas
automatizadas (no mostrado al usuario).

## POST /api/documents

Sube un documento Markdown y crea (o reemplaza) el trabajo de narración de la
sesión actual.

**Request**: `multipart/form-data`
- `file`: archivo `.md` (campo obligatorio)
- Header `X-Session-Token`: identificador de sesión de navegador (ver
  `data-model.md` §1 `session_token`); si falta, el backend genera uno nuevo y
  lo devuelve en la respuesta.

**Comportamiento**:
- Si existe un trabajo previo de la misma sesión en estado `procesando`, se
  cancela y se limpia antes de aceptar el nuevo (FR-031a).
- Valida tamaño en streaming (corta en cuanto se supera 5.000.000 bytes).
- Valida formato (`.md`), codificación UTF-8, idioma español y presencia de
  contenido narrable tras aplicar reglas de omisión.

**Responses**:

| Código | Cuándo | Cuerpo |
|---|---|---|
| `202 Accepted` | Archivo válido, trabajo aceptado | `{ "job_id": "...", "session_token": "...", "nombre_archivo": "...", "estado_procesamiento": "cargando" }` |
| `400` | Petición malformada (sin campo `file`, multipart inválido) | Error estándar |
| `413` | Archivo supera 5.000.000 bytes | Error estándar, `codigo: "tamano_excedido"` |
| `415` | Extensión o formato no admitido (no `.md`, codificación inválida) | Error estándar, `codigo: "formato_incorrecto"` |
| `422` | `.md` válido pero vacío o sin contenido narrable | Error estándar, `codigo: "sin_contenido_narrable"` |

## GET /api/documents/{job_id}/status

Consultado por el frontend mediante sondeo periódico (~1,5 s, ver
`research.md` §5) mientras `estado_procesamiento` no sea terminal.

**Response `200`**:

```json
{
  "job_id": "...",
  "nombre_archivo": "...",
  "estado_procesamiento": "cargando|procesando|listo|error|cancelado",
  "duracion_segundos": null,
  "error": null
}
```

- `duracion_segundos` se completa solo cuando `estado_procesamiento == listo`.
- `error` sigue el formato de error estándar solo cuando
  `estado_procesamiento == error`.

**Responses de error**:

| Código | Cuándo |
|---|---|
| `404` | `job_id` desconocido, ya limpiado (expirado) o de otra sesión |
| `503` | Piper o el modelo de voz no están disponibles en el servidor |

## GET /api/documents/{job_id}/audio

Entrega el audio WAV generado, listo para un elemento `<audio>` del navegador.
Solo responde `200` cuando `estado_procesamiento == listo`.

**Response**: `200 OK`, `Content-Type: audio/wav`, cuerpo binario (soporta
`Range` requests para permitir avance/retroceso en la línea de tiempo, FR-026).

**Responses de error**:

| Código | Cuándo |
|---|---|
| `404` | `job_id` desconocido, expirado, o de otra sesión |
| `409` | El trabajo existe pero aún no está en estado `listo` (todavía `cargando`/`procesando`) |
| `500` | Fallo interno de síntesis no capturado previamente (ver FR-019) |

## DELETE /api/documents/{job_id}

Cancelación explícita por el usuario (por ejemplo, al cerrar/navegar fuera de
la página, FR-031). Limpia inmediatamente los temporales asociados.

**Response**: `204 No Content`.

## Notas de cumplimiento con la constitución

- Ningún endpoint requiere ni acepta claves de proveedores TTS externos.
- Ningún endpoint ejecuta código ni descarga recursos referenciados dentro del
  documento (FR-014).
- `500` se reserva para fallos internos de síntesis; `503` para
  indisponibilidad de Piper/modelo; `504` queda reservado para el caso futuro
  de actuar como gateway de un servicio ascendente (no aplica en esta
  iteración, sin servicios externos).
