# Implementation Plan: Lector de Documentos con Voz

**Branch**: `001-voice-document-reader` | **Date**: 2026-10-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-voice-document-reader/spec.md`

## Summary

Aplicación web de una sola iteración que permite a un usuario subir un documento
Markdown en español (≤5 MB, UTF-8), narrarlo en voz alta en español de España
mediante síntesis local (Piper, `es_ES-davefx-medium`), y reproducirlo en el
navegador con controles estándar (play/pausa, detener, velocidad, línea de
tiempo). El backend en Python (FastAPI) procesa el documento, aplica las reglas
de narración fiel y genera el audio sin enviar texto a proveedores externos; el
frontend en React/TypeScript/Vite/Tailwind consume la API y reproduce el audio.
No hay persistencia permanente: documentos y audios son temporales y se limpian
tras su uso, error, cancelación o pérdida de conexión. Diseñado para un uso
bajo/personal (1-5 usuarios simultáneos, procesamiento secuencial), conforme a
la aclaración registrada en `spec.md`.

## Technical Context

**Language/Version**: Python 3.12 (backend) y TypeScript 5.x sobre Node.js 20
LTS (frontend, vía Vite)

**Primary Dependencies**: Backend: FastAPI, Uvicorn, Piper (motor OHF,
`piper-tts`/`piper1-gpl`), `markdown-it-py` (parser Markdown mantenido con
acceso a tokens/AST), Pydantic. Frontend: React 18, Vite, Tailwind CSS.
Gestión Python exclusivamente con `uv` (`pyproject.toml` + `uv.lock`,
`uv sync --locked`, `uv run`).

**Storage**: N/A — sin base de datos. Solo archivos temporales en disco
(documento subido y audio generado) con limpieza automática; el modelo de voz
Piper (`es_ES-davefx-medium.onnx` + `.onnx.json`) se conserva como recurso de
la aplicación, descargado una vez y versionado aparte de los temporales de
usuario.

**Testing**: Backend: `pytest` + dobles de prueba (stub) para Piper en pruebas
habituales (sin red), con una prueba de escucha manual/real antes de publicar
cambios del motor o modelo; `ruff check`, `ruff format --check`, `mypy`.
Frontend: `vitest` + `@testing-library/react` para componentes y hooks de
reproducción; verificación de compilación (`tsc`/`vite build`).

**Target Platform**: Servidor Linux (backend FastAPI + Piper) y navegador web
de escritorio/portátil moderno (frontend).

**Project Type**: Web application (frontend + backend separados, sin apps
móviles).

**Performance Goals**: Audio listo para reproducirse en menos de 60 s para un
documento de hasta 5 MB (SC-001). Sin objetivos de throughput adicionales dado
el uso bajo/personal.

**Constraints**: Síntesis de voz 100% local/offline tras instalar motor y
modelo (sin llamadas a proveedores TTS externos); límite estricto de archivo de
5.000.000 bytes aplicado durante la carga (no cargar un fichero ilimitado en
memoria); sin autorreproducción; un único audio puede sonar a la vez; sin
persistencia permanente; logs sin contenido de documentos ni credenciales;
frontend y backend MUST ejecutarse en orígenes distintos sin proxy, con la URL
base del backend configurable por entorno vía `VITE_API_BASE_URL` (tiempo de
compilación) y CORS restringido por entorno a los orígenes de frontend
autorizados (`ALLOWED_ORIGINS`), sin que CORS sustituya la validación del
backend (FR-034..FR-039, ver `research.md` §9).

**Scale/Scope**: Uso bajo/personal: 1-5 usuarios simultáneos, procesamiento de
documentos secuencial (una síntesis Piper a la vez es suficiente; ver
Clarifications en `spec.md` y FR-007a). Un único servidor, sin escalado
horizontal en esta iteración.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Regla de la constitución | Estado | Notas |
|---|---|---|
| Frontend React + TypeScript + Vite + Tailwind | ✅ PASS | Definido en Technical Context y Project Structure |
| Backend Python + FastAPI, `multipart/form-data`, audio reproducible sin altavoces del servidor | ✅ PASS | Endpoints en `contracts/` devuelven audio al navegador |
| Gestión Python exclusivamente con `uv` | ✅ PASS | `pyproject.toml` + `uv.lock`; comandos `uv sync --locked` / `uv run` documentados en quickstart |
| Síntesis de voz con Piper (OHF) `es_ES-davefx-medium`, local, sin proveedores externos, offline tras instalar | ✅ PASS | Ver `research.md` (versión de motor/modelo, formato de audio, recursos) |
| No sustituir Piper por `speechSynthesis` | ✅ PASS | No se usa Web Speech API en ningún punto del diseño |
| Licencias de motor/modelo documentadas y aceptadas | ✅ PASS | Documentadas en constitución v2.4.0; referenciadas en `research.md` sin reabrir la decisión |
| Sin base de datos ni persistencia permanente | ✅ PASS | Storage = N/A; limpieza de temporales en `data-model.md`/`quickstart.md` |
| Entrada solo `.md` UTF-8, ≤5 MB, español | ✅ PASS | Validación descrita en `contracts/` y `data-model.md` |
| Lectura fiel y reglas de narración Markdown | ✅ PASS | Mapeadas 1:1 desde spec FR-008..FR-014 a `data-model.md`/`research.md` |
| Voz natural `es_ES-davefx-medium`, prueba de escucha | ✅ PASS | Prueba de escucha definida en `spec.md` SC-003; resultado a registrar en este `plan.md` antes de publicar (ver Pendientes) |
| Controles de reproducción (play/pausa, detener, velocidad, línea de tiempo, teclado) | ✅ PASS | Mapeados desde spec FR-020..FR-028 |
| Privacidad: aviso de envío al backend, sin fallback TTS externo, logs sin contenido | ✅ PASS | FR-029, FR-032, FR-019 |
| Seguridad: no ejecutar código ni descargar enlaces del documento | ✅ PASS | FR-014; reflejado en `research.md` (parser sin ejecución) |
| Archivos temporales: no modificar original, limpieza en fin/fallo/cancelación/pérdida de conexión | ✅ PASS | FR-006, FR-031, FR-031a; detallado en `data-model.md` |
| Estructura simple `/frontend` y `/backend`, sin Clean Architecture ni microservicios | ✅ PASS | Ver Project Structure |
| Responsabilidades separadas (carga/validación, conversión Markdown, motor TTS) en módulos pequeños | ✅ PASS | Ver Project Structure (backend/src/services) |
| Nomenclatura (`snake_case` Python, `camelCase` TS, `PascalCase` componentes) | ✅ PASS | A aplicar en implementación; sin violación de diseño |
| Validación en backend con códigos HTTP semánticos (400/413/415/503/500) | ✅ PASS | Ver `contracts/api.md` |
| Estructura simple `/frontend` y `/backend` como servidores independientes (orígenes distintos) | ✅ PASS | FR-034..FR-039; sin proxy ni microservicio intermedio, ver `research.md` §9 y `contracts/api.md` (sección CORS) |
| Cero código sombra (sin cuentas, pagos, historial, descarga de audio) | ✅ PASS | Confirmado contra Non-Goals de `spec.md` |

No se detectan violaciones que requieran justificación en Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-voice-document-reader/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── uv.lock
├── src/
│   └── lector_documentos/
│       ├── api/                # Endpoints FastAPI (routers)
│       ├── models/              # Esquemas Pydantic (Documento, AudioNarrado, errores)
│       ├── services/
│       │   ├── validation.py    # Formato, codificación, idioma, tamaño (FR-001..FR-007a)
│       │   ├── markdown_narration.py  # Conversión Markdown → texto narrable (FR-008..FR-014)
│       │   ├── tts.py            # Integración Piper (FR-015..FR-019)
│       │   └── cleanup.py        # Limpieza de temporales (FR-030..FR-031a)
│       └── main.py               # Monta `CORSMiddleware` con `ALLOWED_ORIGINS` (FR-037)
├── models/                       # Recurso de aplicación: pesos Piper descargados (no temporales de usuario)
│   ├── es_ES-davefx-medium.onnx
│   └── es_ES-davefx-medium.onnx.json
└── tests/
    ├── unit/
    ├── contract/
    └── integration/

frontend/
├── package.json
├── .env.development / .env.production  # `VITE_API_BASE_URL` por entorno (FR-036)
├── src/
│   ├── components/
│   │   ├── DocumentUploader.tsx
│   │   └── AudioPlayer.tsx       # Play/Pausa, Detener, velocidad, línea de tiempo (FR-020..FR-028)
│   ├── pages/
│   │   └── HomePage.tsx
│   └── services/
│       └── documentsApi.ts       # Cliente de la API; usa `VITE_API_BASE_URL` absoluta (FR-034..FR-038)
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Opción "Web application" de la constitución: dos
proyectos simples, `/backend` (FastAPI + Piper) y `/frontend` (React/Vite), cada
uno con sus propias pruebas junto al código. No se introducen microservicios,
capas de arquitectura limpia ni un framework interno, conforme a la sección 4
de la constitución. El directorio `backend/models/` separa explícitamente el
recurso de aplicación (pesos del modelo de voz) de los temporales de usuario
(documentos/audios), que residirán en un directorio temporal del sistema
operativo gestionado por `cleanup.py`.

## Post-Design Constitution Check

*Re-evaluado tras completar `research.md`, `data-model.md`, `contracts/api.md`
y `quickstart.md` (Phase 1).*

Ninguna decisión de diseño introduce una nueva necesidad de apartarse de la
constitución: el formato de audio WAV, el parser `markdown-it-py`, el sondeo
de estado y la cancelación por sesión son implementaciones concretas de reglas
ya exigidas (no añaden capas, servicios externos, persistencia ni
complejidad no justificada). La comunicación entre orígenes distintos
(`VITE_API_BASE_URL` + `CORSMiddleware`/`ALLOWED_ORIGINS`, FR-034..FR-039,
ver `research.md` §9) tampoco introduce una nueva capa: sustituye una ruta
relativa implícita por una URL absoluta configurable y añade una
configuración de seguridad estándar del propio framework (FastAPI/Starlette),
conservando la estructura simple `/frontend` + `/backend`. **Resultado:
PASS**, sin nuevas entradas en Complexity Tracking.

## Complexity Tracking

> No violations to justify — Constitution Check passed without exceptions.

## Resultados de la prueba de escucha (T064, SC-003)

**Estado: ⏳ PENDIENTE** — requiere un oyente humano real escuchando el audio
generado; no es una verificación que un agente de IA pueda ejecutar ni
certificar por sí mismo.

- **Frases a evaluar**: las definidas en `research.md` §8 (incluyen números y
  siglas).
- **Cómo ejecutarla**: generar el audio de esas frases con el backend en
  marcha (`POST /api/documents` con un `.md` que las contenga, luego
  reproducir `GET /{job_id}/audio`), y que una persona registre el porcentaje
  de palabras identificadas correctamente.
- **A registrar aquí antes de publicar**: oyente, fecha, % identificado,
  observaciones.

Verificación técnica ya realizada (no sustituye la prueba de escucha humana,
pero confirma que el pipeline de síntesis funciona correctamente): el 2026-10-08
se generó y reprodujo un audio de prueba con el backend real; el archivo
resultante es un WAV PCM de 16 bits, mono, 22.050 Hz, válido y reproducible
(verificado con `file`), y el servidor respondió correctamente a peticiones
`Range` (ver `quickstart.md`, sección "Resultados de la validación").

## Confirmación de versiones y licencias (T065, constitución §2)

- **Motor**: paquete PyPI `piper-tts` (proyecto GitHub `OHF-voice/piper1-gpl`)
  — ver `backend/pyproject.toml`. Versión fijada por `backend/uv.lock`
  (`uv sync --locked` instala exactamente esta versión).
- **Modelo de voz**: `es_ES-davefx-medium` (español de España, calidad media),
  descargado en `backend/models/es_ES-davefx-medium.onnx` +
  `.onnx.json`.
- **Formato de audio**: WAV PCM 16-bit, mono, 22.050 Hz (verificado
  empíricamente en la validación de `quickstart.md`).
- **Licencias**:
  - El motor Piper se distribuye bajo **GPL-3.0**. Si este backend se
    redistribuye junto con el binario/paquete de Piper, deben cumplirse las
    obligaciones de la GPL-3.0 (código fuente disponible, misma licencia para
    la obra derivada que incorpore Piper, aviso de licencia).
  - La licencia específica de los **pesos** del modelo `es_ES-davefx-medium`
    (distinta de la licencia del motor) **no se confirma en este documento**:
    debe verificarse en el repositorio/página de descarga del modelo
    (Hugging Face `rhasspy/piper-voices` u origen equivalente) antes de
    redistribuir el modelo descargado, conforme a la constitución sección 2 y
    a los "Pendientes Antes de Publicar" de `spec.md`. Esta confirmación
    requiere una revisión legal/humana explícita y queda **pendiente**.

