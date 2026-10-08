# Data Model: Lector de Documentos con Voz

**Fecha**: 2026-10-08 | **Fuente**: `spec.md` (Key Entities), `research.md`

Todas las entidades son **temporales**: ninguna se persiste en base de datos.
Viven en memoria de proceso y/o en un directorio temporal del sistema
operativo durante el ciclo de vida de un trabajo de narración, y se eliminan
según las reglas de limpieza (FR-030, FR-031, FR-031a).

## 1. Documento

Representa el archivo Markdown subido por el usuario para una narración.

| Campo | Tipo | Descripción / Reglas |
|---|---|---|
| `job_id` | string (UUID) | Identificador único del trabajo de narración; generado al aceptar la subida. |
| `session_token` | string | Identifica la sesión de navegador propietaria del trabajo; usado para aplicar FR-031a (cancelar trabajo previo de la misma sesión). |
| `nombre_archivo` | string | Nombre original del archivo, mostrado en la interfaz (FR-005). No se usa como ruta de almacenamiento directa (evitar path traversal). |
| `tamano_bytes` | integer | Tamaño del archivo recibido. MUST ser `<= 5_000_000`; de lo contrario, estado `rechazado` con motivo `tamano_excedido` (FR-003). |
| `codificacion_valida` | boolean | Resultado de validar UTF-8 (FR-002, FR-007). |
| `idioma_valido` | boolean | Resultado de detectar contenido narrable en español (FR-002, FR-007). |
| `tiene_contenido_narrable` | boolean | `false` si, tras aplicar las reglas de omisión (FR-010..FR-013), no queda ningún texto narrable (FR-004). |
| `estado_validacion` | enum: `valido` \| `rechazado` | Resultado consolidado de validar formato, codificación, idioma, tamaño y contenido narrable. |
| `motivo_rechazo` | enum (nullable): `formato_incorrecto` \| `tamano_excedido` \| `vacio_o_sin_contenido_narrable` \| `codificacion_invalida` \| `idioma_no_valido` | Solo presente si `estado_validacion = rechazado`; usado para el mensaje de error (FR-033, SC-002). |
| `estado_procesamiento` | enum: `cargando` \| `procesando` \| `listo` \| `error` \| `cancelado` | Expuesto al frontend para FR-005/FR-018. |
| `ruta_temporal` | string (interna, no expuesta a la API) | Ubicación en disco del archivo original sin modificar (FR-006), gestionada por `cleanup.py`. |
| `creado_en` | datetime | Marca de tiempo de aceptación, usada por la limpieza por expiración (SC-005: nada accesible tras 5 min de finalizar la sesión). |

**Reglas de transición de estado** (`estado_procesamiento`):

`cargando → procesando → (listo | error)`; en cualquier punto puede pasar a
`cancelado` si llega un nuevo documento de la misma sesión (FR-031a) o si el
usuario cancela explícitamente / se pierde la conexión (FR-031).
`cancelado` y `error` son estados terminales que disparan limpieza inmediata
de `ruta_temporal` y de cualquier audio parcial.

## 2. Audio Narrado

Representa el resultado de la síntesis de voz asociado a un `Documento`.

| Campo | Tipo | Descripción / Reglas |
|---|---|---|
| `job_id` | string (UUID) | Mismo identificador que el `Documento` de origen (relación 1:1). |
| `ruta_temporal` | string (interna) | Ubicación del archivo WAV generado por Piper (ver `research.md` §2). |
| `duracion_segundos` | float (nullable) | Duración total; `null` hasta que la generación termine. Mostrada en la línea de tiempo (FR-026). |
| `estado` | enum: `generando` \| `listo` \| `error` | Refleja el progreso de síntesis (FR-018, FR-019). |
| `motivo_error` | string (nullable) | Mensaje interno (no expuesto tal cual al usuario) cuando `estado = error`; se traduce a un mensaje comprensible según FR-033. |

**Relación**: Un `Audio narrado` pertenece exactamente a un `Documento`
(`job_id` compartido); eliminar/cancelar el `Documento` MUST eliminar también
su `Audio narrado` asociado (FR-031, FR-031a).

## 3. Sesión de Reproducción

Representa el estado de reproducción en el navegador; **no existe en el
backend**, es estado de cliente (React) derivado del elemento `<audio>` del
DOM. Se documenta aquí porque forma parte del modelo de datos funcional de la
spec (Key Entities) y porque un único `Audio narrado` puede estar asociado a
una sesión de reproducción activa a la vez en todo el navegador (FR-028).

| Campo | Tipo | Descripción / Reglas |
|---|---|---|
| `job_id_activo` | string (nullable) | `job_id` del audio actualmente cargado en el reproductor; solo puede haber uno a la vez en toda la aplicación (FR-028). |
| `posicion_segundos` | float | Posición actual de reproducción; se preserva al pausar (FR-022) y se restablece a `0` al detener (FR-023). |
| `estado_reproduccion` | enum: `detenido` \| `reproduciendo` \| `en_pausa` | Controla qué acciones están disponibles y el ícono del botón Play/Pausa. |
| `velocidad` | enum: `0.75` \| `1` \| `1.25` \| `1.5` \| `2` | Valor por defecto `1` (FR-024); cambiarla MUST NOT regenerar audio ni reiniciar `posicion_segundos` (FR-025). |
| `controles_habilitados` | boolean | `false` hasta que `Audio narrado.estado == listo` (FR-027). |

**Invariante de unicidad**: Iniciar la reproducción de un nuevo `job_id` MUST
detener (`estado_reproduccion = detenido`, liberar `job_id_activo`) cualquier
reproducción en curso de otro `job_id` antes de activarse (FR-028, SC-007).

## 4. Limpieza y expiración (transversal)

No es una entidad de datos sino una regla aplicada sobre `Documento` y
`Audio narrado`:

- Al llegar a un estado terminal (`listo` consumido y sesión finalizada,
  `error`, `cancelado`), o transcurridos 5 minutos desde la finalización de la
  sesión de narración (SC-005), se eliminan `ruta_temporal` de ambas
  entidades.
- La pérdida de conexión se detecta por el cierre de la conexión HTTP de
  sondeo/streaming; dispara el mismo flujo de limpieza que una cancelación
  explícita (FR-031).
- El modelo de voz Piper (`backend/models/es_ES-davefx-medium.*`) está
  explícitamente excluido de esta limpieza: es un recurso de aplicación de
  larga duración, no un temporal de usuario (ver `research.md` §2 y
  constitución sección 2).
