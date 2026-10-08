# Tasks: Lector de Documentos con Voz

**Input**: Design documents from `/specs/001-voice-document-reader/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Incluidas explícitamente — la constitución del proyecto (sección 5,
"Pruebas") exige cubrir carga, conversión, errores del motor y controles de
audio, por lo que cada historia de usuario incluye tareas de prueba antes de
su implementación.

**Organization**: Tareas agrupadas por historia de usuario (spec.md) para
permitir implementación y prueba independientes de cada una.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivo distinto, sin dependencias pendientes)
- **[Story]**: Historia de usuario a la que pertenece (US1, US2, US3, US4)
- Rutas de archivo exactas incluidas en cada descripción

## Path Conventions

Web app (ver `plan.md` → Project Structure): `backend/src/`, `backend/tests/`,
`frontend/src/`, `frontend/tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto y estructura básica

- [ ] T001 Create project structure per `plan.md` (`backend/`, `frontend/`, `backend/tests/{unit,contract,integration}`, `frontend/tests/{unit,integration}`)
- [ ] T002 [P] Initialize backend Python project: `backend/pyproject.toml` declarando `requires-python = ">=3.12,<3.13"` y dependencias `fastapi`, `uvicorn`, `pydantic`, `markdown-it-py`, `piper1-gpl` (research.md §1-3); generar `backend/uv.lock` con `uv sync`
- [ ] T003 [P] Initialize frontend Vite+React+TypeScript+Tailwind project: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js` (plan.md Technical Context)
- [ ] T004 [P] Configure backend tooling (`ruff`, `mypy`) in `backend/pyproject.toml`
- [ ] T005 [P] Configure frontend tooling (eslint/prettier) and `vitest` in `frontend/package.json`, `frontend/vitest.config.ts` (research.md §4)
- [ ] T006 Download Piper voice model files into `backend/models/es_ES-davefx-medium.onnx` and `backend/models/es_ES-davefx-medium.onnx.json` per `quickstart.md` Prerrequisitos

**Checkpoint**: Estructura de ambos proyectos lista para desarrollo.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura central que TODAS las historias de usuario necesitan

**⚠️ CRITICAL**: Ninguna historia de usuario puede comenzar hasta completar esta fase

- [ ] T007 [P] Define `Documento` and `AudioNarrado` Pydantic schemas with the exact fields, enum values (`estado_validacion`: `valido`|`rechazado`; `motivo_rechazo`: `formato_incorrecto`|`tamano_excedido`|`vacio_o_sin_contenido_narrable`|`codificacion_invalida`|`idioma_no_valido`; `estado_procesamiento`: `cargando`|`procesando`|`listo`|`error`|`cancelado`; `Audio narrado.estado`: `generando`|`listo`|`error`) and constraint `tamano_bytes <= 5_000_000` from `data-model.md` §1-2 in `backend/src/lector_documentos/models/schemas.py`
- [ ] T008 Implement in-memory job store enforcing a single active job per `session_token`, with the state transitions `cargando → procesando → (listo | error)` and `→ cancelado` from `data-model.md` §1, depends on T007, in `backend/src/lector_documentos/services/job_store.py`
- [ ] T009 [P] Implement the standard error schema `{ "error": { "codigo": "string", "mensaje": "string" } }` and FastAPI exception handlers per `contracts/api.md` in `backend/src/lector_documentos/api/errors.py`
- [ ] T010 Create FastAPI application skeleton with router registration and a startup check that verifies Piper and the voice model are loadable (feeds the `503` case in `contracts/api.md`), depends on T007, T009, in `backend/src/lector_documentos/main.py`
- [ ] T011 Implement a temp-file manager for per-job directories (distinct from `backend/models/`, per `data-model.md` §4), with deletion hooks used by finish/fail/cancel flows (FR-006, FR-030, FR-031), depends on T008, in `backend/src/lector_documentos/services/cleanup.py`
- [ ] T012 [P] Create frontend API client with session-token header handling (`X-Session-Token` per `contracts/api.md`) in `frontend/src/services/documentsApi.ts`
- [ ] T013 Scaffold `HomePage` composing `DocumentUploader` and `AudioPlayer` placeholders, depends on T012, in `frontend/src/pages/HomePage.tsx`

**Checkpoint**: Infraestructura base lista — las historias de usuario pueden comenzar.

---

## Phase 3: User Story 1 - Subir un documento y escuchar su narración (Priority: P1) 🎯 MVP

**Goal**: Un usuario sube un `.md` válido en español y puede reproducir su narración completa en el orden correcto.

**Independent Test**: Subir un `.md` válido, esperar a que el estado pase a "listo" y reproducir el audio verificando el orden y la ausencia de marcas Markdown pronunciadas.

### Tests for User Story 1 ⚠️

> Escribir estas pruebas PRIMERO; deben fallar antes de implementar

- [ ] T014 [P] [US1] Contract test: `POST /api/documents` happy path returns `202` with `job_id` per `contracts/api.md` in `backend/tests/contract/test_documents_post.py`
- [ ] T015 [P] [US1] Contract test: `GET /api/documents/{job_id}/status` happy-path transitions (`cargando`→`procesando`→`listo`) in `backend/tests/contract/test_documents_status.py`
- [ ] T016 [P] [US1] Contract test: `GET /api/documents/{job_id}/audio` happy path returns `200` `audio/wav` and supports `Range` requests in `backend/tests/contract/test_documents_audio.py`
- [ ] T017 [P] [US1] Integration test: full upload→poll→listo flow for a valid Spanish `.md` completes within the SC-001 target in `backend/tests/integration/test_upload_narrate_flow.py`
- [ ] T018 [P] [US1] Integration test: uploading a second document for the same session cancels the first job's processing and cleans its temp files (FR-031a) in `backend/tests/integration/test_cancel_on_new_upload.py`
- [ ] T019 [P] [US1] Frontend integration test: uploader shows filename and `cargando`/`procesando`/`listo` states plus the privacy notice (FR-005, FR-029) in `frontend/tests/integration/DocumentUploader.test.tsx`
- [ ] T020 [P] [US1] Frontend integration test: Play requires an explicit click (no autoplay) and starts narration from the first block (FR-020, FR-021) in `frontend/tests/integration/AudioPlayer.test.tsx`

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement Markdown narration service for headings/paragraphs/quotes/lists with a perceptible pause between blocks, without pronouncing Markdown syntax markers (FR-008, FR-009), using `markdown-it-py` tokens (research.md §3), in `backend/src/lector_documentos/services/markdown_narration.py`
- [ ] T022 [P] [US1] Implement Piper TTS integration producing a 16-bit mono 22.050 Hz WAV file locally/offline, no external TTS calls (FR-015, FR-016, FR-017), in `backend/src/lector_documentos/services/tts.py`
- [ ] T023 [US1] Implement the sequential processing pipeline (validate→parse→narrate→synthesize→`listo`, a single job in flight at a time per FR-007a), depends on T021, T022, in `backend/src/lector_documentos/services/pipeline.py`
- [ ] T024 [US1] Implement `POST /api/documents`: accept the multipart upload, keep the original file unmodified (FR-006), cancel and clean any prior in-flight job of the same session before accepting (FR-031a), and enqueue the pipeline, depends on T023, in `backend/src/lector_documentos/api/documents.py`
- [ ] T025 [US1] Implement `GET /api/documents/{job_id}/status` per `contracts/api.md`, depends on T024, in `backend/src/lector_documentos/api/documents.py`
- [ ] T026 [US1] Implement `GET /api/documents/{job_id}/audio` with `Range` support per `contracts/api.md`, depends on T024, in `backend/src/lector_documentos/api/documents.py`
- [ ] T027 [P] [US1] Implement `DocumentUploader` component: file picker, filename/status display, and the privacy notice that the document is sent to the backend (FR-005, FR-029) in `frontend/src/components/DocumentUploader.tsx`
- [ ] T028 [P] [US1] Implement a status-polling hook (~1.5 s interval per research.md §5) in `frontend/src/services/documentsApi.ts`
- [ ] T029 [US1] Implement the `AudioPlayer` base: load the audio source only once `listo`, Play requires an explicit click, no autoplay (FR-020, FR-021), depends on T028, in `frontend/src/components/AudioPlayer.tsx`

**Checkpoint**: User Story 1 completamente funcional y verificable de forma independiente (MVP).

---

## Phase 4: User Story 2 - Controlar la reproducción del audio (Priority: P2)

**Goal**: El usuario puede pausar, reanudar, detener, cambiar la velocidad y desplazarse en la línea de tiempo.

**Independent Test**: Con un audio de prueba ya listo, validar cada control (play/pausa, detener, velocidad, línea de tiempo) de forma aislada.

### Tests for User Story 2 ⚠️

- [ ] T030 [P] [US2] Unit tests for `AudioPlayer` controls: Play/Pausa preserves position on resume, Detener resets to 0, speed change applies `playbackRate` without reload/reset, timeline shows elapsed/total and seeking updates position, controls stay disabled until `listo` (FR-022..FR-027) in `frontend/tests/unit/AudioPlayer.test.tsx`
- [ ] T031 [P] [US2] Integration test: starting playback of a new document stops any other currently playing audio (FR-028, SC-007) in `frontend/tests/integration/SinglePlaybackGuard.test.tsx`

### Implementation for User Story 2

- [ ] T032 [US2] Implement Play/Pausa toggle preserving the current position on resume (FR-022) in `frontend/src/components/AudioPlayer.tsx`
- [ ] T033 [US2] Implement Detener control resetting the position to 0 (FR-023), depends on T032, in `frontend/src/components/AudioPlayer.tsx`
- [ ] T034 [US2] Implement the speed selector (`0.75x`, `1x`, `1.25x`, `1.5x`, `2x`; default `1x`) via `playbackRate`, without regenerating the audio or resetting the position (FR-024, FR-025), depends on T032, in `frontend/src/components/AudioPlayer.tsx`
- [ ] T035 [US2] Implement the timeline showing elapsed/total time with drag/click seek (FR-026), depends on T032, in `frontend/src/components/AudioPlayer.tsx`
- [ ] T036 [US2] Disable controls until the audio is `listo`; ensure keyboard operability with ARIA labels (FR-027), depends on T032-T035, in `frontend/src/components/AudioPlayer.tsx`
- [ ] T037 [P] [US2] Implement a single-active-playback guard that stops any other audio when a new one starts (FR-028) in `frontend/src/services/playbackGuard.ts`

**Checkpoint**: User Story 1 y 2 funcionan de forma independiente y conjunta.

---

## Phase 5: User Story 3 - Manejo de contenido no narrable y elementos especiales (Priority: P2)

**Goal**: Enlaces, imágenes, tablas y elementos no narrables se tratan según las reglas de fidelidad, sin romper la narración.

**Independent Test**: Documentos de prueba con cada tipo de elemento especial, verificando el comportamiento esperado de cada uno de forma aislada del resto de historias.

### Tests for User Story 3 ⚠️

- [ ] T038 [P] [US3] Unit test: links narrate the visible text, never the URL (FR-010) in `backend/tests/unit/test_markdown_narration_links.py`
- [ ] T039 [P] [US3] Unit test: images with alt text narrate only the alt text; images without alt text narrate nothing (FR-011) in `backend/tests/unit/test_markdown_narration_images.py`
- [ ] T040 [P] [US3] Unit test: tables narrate column headers first, then each row's cells left-to-right (FR-012) in `backend/tests/unit/test_markdown_narration_tables.py`
- [ ] T041 [P] [US3] Unit test: inline code, code blocks, bare URLs, thematic breaks, and raw HTML are omitted without being executed or rendered (FR-013, FR-014) in `backend/tests/unit/test_markdown_narration_omissions.py`

### Implementation for User Story 3

- [ ] T042 [US3] Extend `markdown_narration.py` to narrate a link's visible text only (FR-010), depends on T021, in `backend/src/lector_documentos/services/markdown_narration.py`
- [ ] T043 [US3] Extend `markdown_narration.py` to narrate only an image's alt text, omitting images without it (FR-011), depends on T042, in `backend/src/lector_documentos/services/markdown_narration.py`
- [ ] T044 [US3] Extend `markdown_narration.py` to narrate tables by row, headers first, left-to-right (FR-012), depends on T043, in `backend/src/lector_documentos/services/markdown_narration.py`
- [ ] T045 [US3] Extend `markdown_narration.py` to omit inline code, code blocks, bare URLs, thematic breaks, and raw HTML without executing or rendering them (FR-013, FR-014), depends on T044, in `backend/src/lector_documentos/services/markdown_narration.py`

**Checkpoint**: User Stories 1, 2 y 3 funcionan de forma independiente.

---

## Phase 6: User Story 4 - Validación de documentos y manejo de errores (Priority: P3)

**Goal**: Archivos inválidos o fallos del motor de voz producen mensajes de error claros y comprensibles.

**Independent Test**: Subir archivos inválidos de cada tipo y forzar un fallo del motor de voz, verificando el mensaje de error específico de cada caso.

### Tests for User Story 4 ⚠️

- [ ] T046 [P] [US4] Contract test: non-`.md` upload returns `415` with `codigo: "formato_incorrecto"` (FR-002) in `backend/tests/contract/test_documents_post_invalid_format.py`
- [ ] T047 [P] [US4] Contract test: file exceeding 5,000,000 bytes returns `413` with `codigo: "tamano_excedido"` (FR-003) in `backend/tests/contract/test_documents_post_oversize.py`
- [ ] T048 [P] [US4] Contract test: empty or no-narrable-content `.md` returns `422` with `codigo: "sin_contenido_narrable"` (FR-004) in `backend/tests/contract/test_documents_post_empty.py`
- [ ] T049 [P] [US4] Contract test: Piper/model unavailable returns `503` without an automatic fallback provider (FR-019) in `backend/tests/contract/test_documents_status_tts_failure.py`
- [ ] T050 [P] [US4] Frontend integration test: each backend error `codigo` renders a comprehensible message without technical details (FR-033) in `frontend/tests/integration/ErrorHandling.test.tsx`

### Implementation for User Story 4

- [ ] T051 [P] [US4] Implement extension/format validation (`.md` only) (FR-002) in `backend/src/lector_documentos/services/validation.py`
- [ ] T052 [US4] Implement UTF-8 encoding validation (FR-002, FR-007), depends on T051, in `backend/src/lector_documentos/services/validation.py`
- [ ] T053 [US4] Implement Spanish narrable-content language detection (FR-002, FR-007), depends on T052, in `backend/src/lector_documentos/services/validation.py`
- [ ] T054 [US4] Implement streaming size-limit enforcement cutting the upload at 5,000,000 bytes without buffering the whole file in memory (FR-003), depends on T053, in `backend/src/lector_documentos/services/validation.py`
- [ ] T055 [US4] Implement empty/no-narrable-content detection applied after the omission rules from User Story 3 (FR-004), depends on T054, T045, in `backend/src/lector_documentos/services/validation.py`
- [ ] T056 [US4] Wire the validation service into `POST /api/documents`, returning `400`/`413`/`415`/`422` with `{codigo, mensaje}` per `contracts/api.md` (FR-033), depends on T055, T024, in `backend/src/lector_documentos/api/documents.py`
- [ ] T057 [P] [US4] Implement Piper failure handling returning `503` (engine/model unavailable) or `500` (internal synthesis failure) without an automatic fallback provider (FR-019), depends on T022, in `backend/src/lector_documentos/services/tts.py`
- [ ] T058 [P] [US4] Implement the frontend `ErrorBanner` component translating backend `{codigo, mensaje}` into comprehensible UI messages (FR-033) in `frontend/src/components/ErrorBanner.tsx`

**Checkpoint**: Las cuatro historias de usuario funcionan de forma independiente.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Mejoras que afectan a varias historias de usuario

- [ ] T059 [P] Configure structured logging that excludes document content and credentials (FR-032) in `backend/src/lector_documentos/main.py`
- [ ] T060 [P] Implement a temp-file expiry sweep removing job artifacts 5 minutes after the narration session ends (SC-005), depends on T011, in `backend/src/lector_documentos/services/cleanup.py`
- [ ] T061 [P] Document backend quality-gate commands (`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`) in `backend/README.md`
- [ ] T062 [P] Document frontend quality-gate commands (`vitest`, `tsc --noEmit`, `vite build`) in `frontend/package.json` scripts and `frontend/README.md`
- [ ] T063 Run all `quickstart.md` validation scenarios end-to-end and record the results in `specs/001-voice-document-reader/quickstart.md`
- [ ] T064 Execute the Piper listening test defined in `research.md` §8 and record the results (oyente, fecha, % identificado) in `specs/001-voice-document-reader/plan.md`
- [ ] T065 [P] Confirm and document the final engine/model versions, audio format, and license-evidence summary in `specs/001-voice-document-reader/plan.md` per constitución §2

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias — puede comenzar de inmediato
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEA todas las historias de usuario
- **User Stories (Phase 3-6)**: Todas dependen de Foundational
  - US1 (P1) no depende de otras historias
  - US2 (P2) depende de que exista un `AudioPlayer` básico (T029 de US1) para extender sus controles
  - US3 (P2) depende de que exista `markdown_narration.py` (T021 de US1) para extenderlo
  - US4 (P3) depende de la tubería de procesamiento (US1) y de las reglas de omisión (US3, para T055) para detectar "sin contenido narrable"
- **Polish (Phase 7)**: Depende de que las historias deseadas estén completas

### User Story Dependencies

- **US1 (P1)**: Independiente tras Foundational — es el MVP
- **US2 (P2)**: Extiende el `AudioPlayer` creado en US1; no bloquea ni es bloqueada por US3
- **US3 (P2)**: Extiende `markdown_narration.py` creado en US1; no bloquea ni es bloqueada por US2
- **US4 (P3)**: Se apoya en la tubería de US1 y en las reglas de omisión de US3 para la detección de contenido vacío; el resto de validaciones son independientes

### Parallel Opportunities

- Todas las tareas `[P]` de Setup (T002-T005) en paralelo
- T007, T009, T012 de Foundational en paralelo (archivos distintos)
- Todas las pruebas `[P]` de una misma historia (archivos distintos) en paralelo antes de su implementación
- T021 y T022 (narración y TTS) en paralelo dentro de US1
- US2 y US3 pueden desarrollarse en paralelo por personas distintas una vez completada US1 (tocan archivos distintos: `AudioPlayer.tsx` vs `markdown_narration.py`)

---

## Parallel Example: User Story 1

```bash
# Lanzar todas las pruebas de User Story 1 juntas:
Task: "Contract test POST /api/documents happy path in backend/tests/contract/test_documents_post.py"
Task: "Contract test GET /api/documents/{job_id}/status in backend/tests/contract/test_documents_status.py"
Task: "Contract test GET /api/documents/{job_id}/audio in backend/tests/contract/test_documents_audio.py"
Task: "Integration test full upload→poll→listo flow in backend/tests/integration/test_upload_narrate_flow.py"
Task: "Integration test cancel-on-new-upload in backend/tests/integration/test_cancel_on_new_upload.py"
Task: "Frontend integration test DocumentUploader states in frontend/tests/integration/DocumentUploader.test.tsx"
Task: "Frontend integration test Play requires explicit click in frontend/tests/integration/AudioPlayer.test.tsx"

# Lanzar los dos servicios independientes de User Story 1 juntos:
Task: "Markdown narration service in backend/src/lector_documentos/services/markdown_narration.py"
Task: "Piper TTS integration in backend/src/lector_documentos/services/tts.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (CRÍTICO — bloquea todas las historias)
3. Completar Phase 3: User Story 1
4. **DETENER Y VALIDAR**: probar User Story 1 de forma independiente con `quickstart.md` §3
5. Desplegar/demostrar si está listo

### Incremental Delivery

1. Setup + Foundational → base lista
2. Añadir US1 → probar de forma independiente → demo (¡MVP!)
3. Añadir US2 (controles) y US3 (elementos especiales) en paralelo → probar cada una de forma independiente
4. Añadir US4 (validación y errores) → probar de forma independiente
5. Phase 7: Polish, prueba de escucha y validación final de `quickstart.md`

### Parallel Team Strategy

Con varios desarrolladores:

1. El equipo completa Setup + Foundational en conjunto
2. Una persona completa US1 (MVP)
3. Con US1 lista, dos personas en paralelo: una en US2 (controles de reproducción), otra en US3 (reglas de narración de elementos especiales)
4. Una persona en US4 una vez que la tubería (US1) y las reglas de omisión (US3) estén disponibles

---

## Notes

- `[P]` = archivos distintos, sin dependencias pendientes
- La etiqueta `[Story]` traza cada tarea a su historia de usuario de `spec.md`
- Cada historia de usuario debe ser completable y verificable de forma independiente
- Verificar que las pruebas fallan antes de implementar (TDD)
- Confirmar al terminar cada tarea o grupo lógico
- Detenerse en cada checkpoint para validar la historia de forma independiente
- Evitar: tareas vagas, conflictos en el mismo archivo marcados como `[P]`, dependencias cruzadas entre historias que rompan su independencia
