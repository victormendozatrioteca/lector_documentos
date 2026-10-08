# Phase 0 Research: Lector de Documentos con Voz

**Fecha**: 2026-10-08
**Spec**: [spec.md](./spec.md) | **Constitución**: v2.4.0

Todos los puntos abajo estaban como decisión implícita en la constitución del
proyecto o como vacío de "Technical Context"; este documento los deja
explícitos y justificados para que `/speckit-tasks` pueda descomponerlos sin
ambigüedad. No quedan marcadores `NEEDS CLARIFICATION`.

## 1. Versión de Python y gestión de dependencias

- **Decision**: Python 3.12, gestionado exclusivamente con `uv`
  (`pyproject.toml` declara `requires-python = ">=3.12,<3.13"`; `uv.lock`
  versionado; `uv sync --locked` para instalar, `uv run <cmd>` para ejecutar).
- **Rationale**: 3.12 es la última versión estable con soporte activo al
  momento de este plan, con mejoras de rendimiento relevantes para el
  procesamiento de texto/audio. La constitución exige declarar la versión en
  `pyproject.toml` pero no fija un número; 3.12 es el valor por defecto más
  seguro y mantenible.
- **Alternatives considered**: Python 3.11 (más probado, pero sin las mejoras
  de 3.12); Python 3.13 (demasiado reciente para garantizar compatibilidad
  inmediata con todas las dependencias de Piper/ONNX Runtime).

## 2. Motor y modelo de síntesis de voz (Piper)

- **Decision**: Motor Piper mantenido por OHF (`piper1-gpl`, licencia
  GPL-3.0), modelo de voz `es_ES-davefx-medium` (dataset CC0, variante
  `es_ES`, calidad media, un hablante, 22.050 Hz). Formato de audio de salida:
  WAV (PCM 16-bit, mono, 22.050 Hz) generado directamente por Piper; se sirve
  tal cual al navegador vía `<audio>` (sin reencodear a MP3/Opus en esta
  iteración, para mantener la cadena de procesamiento simple).
- **Rationale**: Esta elección ya es una decisión explícita y no negociable de
  la constitución (sección 2 y 6); este documento solo registra las versiones
  y evidencias concretas para trazabilidad en el plan, como exige la
  constitución ("Documentar en `plan.md` la version del motor, modelo..."). WAV
  evita dependencias adicionales de codificación y es reproducible nativamente
  por todos los navegadores soportados.
- **Alternatives considered**: Reencodear a MP3/Opus para reducir tamaño de
  transferencia — rechazado por ahora (YAGNI, documentos ≤5 MB producen audios
  de duración acotada; añadiría una dependencia de codificación sin un
  requisito medible que lo justifique). `speechSynthesis` del navegador —
  explícitamente prohibido por la constitución.
- **Licencias**: Ver constitución v2.4.0 sección 2 para el detalle completo
  (CC0 del dataset, incertidumbre documentada sobre la licencia específica de
  los pesos, GPL-3.0 del motor y sus obligaciones de redistribución). Este
  plan no redistribuye el motor ni el modelo fuera del propio servidor en esta
  iteración (solo se ejecuta localmente), por lo que no se activan las
  obligaciones de distribución de GPL-3.0 en este alcance; deberá revisarse de
  nuevo antes de publicar una imagen Docker distribuible.
- **Recursos necesarios**: CPU (Piper funciona en CPU sin GPU); ~tamaño del
  modelo `es_ES-davefx-medium` (decenas de MB) descargado una vez en
  `backend/models/` y versionado como recurso de aplicación (no es un
  temporal de usuario); sin requisitos de GPU ni aceleración especial dado el
  volumen bajo/personal (1-5 usuarios simultáneos).

## 3. Parser de Markdown para narración fiel

- **Decision**: `markdown-it-py` (parser Python activamente mantenido, usado
  en producción por proyectos como Jupyter/MyST).
- **Rationale**: Expone un flujo de tokens estructurado (encabezados,
  párrafos, listas, citas, tablas, enlaces, imágenes, código en línea/bloque,
  HTML crudo, líneas separadoras) que permite implementar exactamente las
  reglas de narración de FR-008 a FR-014 sin tener que renderizar a HTML y
  volver a parsear. No ejecuta ni evalúa el contenido (cumple FR-014 y la
  regla de seguridad de la constitución: tratar el archivo como datos no
  confiables).
- **Alternatives considered**: `python-markdown` (extensible pero orientado a
  salida HTML, requiere trabajo extra para recuperar estructura narrable
  limpia); `mistune` (rápido, pero su AST es menos estable entre versiones
  mayores para las reglas de tabla/HTML crudo que necesitamos).

## 4. Framework de pruebas del frontend

- **Decision**: `vitest` + `@testing-library/react` para pruebas unitarias y
  de integración de componentes (uploader, reproductor); verificación de tipos
  con `tsc --noEmit` y build con `vite build` como parte de "pruebas y
  compilación del frontend" exigidas por la constitución.
- **Rationale**: Integración nativa con Vite (mismo motor de transformación,
  arranque rápido, sin configuración adicional de bundler), y
  `@testing-library/react` favorece probar comportamiento accesible (foco,
  teclado, roles ARIA) en línea con FR-027.
- **Alternatives considered**: Jest (requiere configuración adicional para
  Vite/ESM); Cypress/Playwright component testing (añaden una dependencia E2E
  pesada no justificada para esta iteración de bajo volumen).

## 5. Estrategia de procesamiento asíncrono y progreso

- **Decision**: Flujo de dos pasos sobre HTTP: (1) `POST` de subida que valida
  y encola el documento, devolviendo un identificador de trabajo de forma
  inmediata (202 Accepted); (2) el frontend sondea (`polling`) un endpoint de
  estado (`cargando/procesando/listo/error`) cada ~1-2 s hasta que el audio
  esté listo o falle, cumpliendo FR-005 y FR-018. El procesamiento en sí
  (parseo + síntesis Piper) se ejecuta de forma secuencial en el backend (una
  tarea en vuelo a la vez), suficiente para el objetivo de 1-5 usuarios
  simultáneos (ver Clarifications en `spec.md`).
- **Rationale**: Evita que una request HTTP quede abierta hasta 60 s (riesgo
  de timeouts de proxies/navegador) y permite mostrar el estado "generando
  audio" exigido explícitamente por FR-018, con la complejidad mínima
  justificable (sin colas distribuidas, sin websockets) para el volumen
  acordado.
- **Alternatives considered**: Respuesta síncrona bloqueante (más simple, pero
  no permite mostrar progreso y arriesga timeouts); WebSockets/Server-Sent
  Events para progreso en tiempo real (mayor complejidad no justificada por
  los requisitos actuales — se puede reconsiderar si el volumen crece).

## 6. Cancelación y limpieza al subir un nuevo documento (FR-031a)

- **Decision**: Cada sesión de navegador mantiene como máximo un "trabajo"
  activo en el backend, identificado por un token de sesión/trabajo generado
  en el primer `POST`. Si llega un nuevo `POST` para la misma sesión mientras
  el trabajo anterior sigue en estado `procesando`, el backend cancela la
  tarea en curso (señal de cancelación cooperativa revisada entre pasos de
  parseo/síntesis), limpia inmediatamente sus archivos temporales, y arranca
  el nuevo trabajo.
- **Rationale**: Implementa directamente la aclaración registrada en `spec.md`
  (Clarifications, pregunta 2) con el mecanismo más simple disponible en
  FastAPI (sin infraestructura de colas externa), acorde al volumen bajo.
- **Alternatives considered**: Permitir múltiples trabajos en paralelo por
  sesión (rechazado: contradice la aclaración y la regla de "un único audio
  puede sonar a la vez"); usar una cola de verdad (Celery/RQ) — rechazado por
  sobreingeniería para 1-5 usuarios simultáneos.

## 7. Límites y tiempos de espera

- **Decision**: Límite de carga aplicado en streaming durante la recepción
  del `multipart/form-data` (cortar y responder `413` en cuanto se superan
  5.000.000 bytes, sin acumular el archivo completo en memoria primero).
  Tiempo máximo de procesamiento por documento: 90 s de margen operativo sobre
  el objetivo de 60 s de SC-001 (se responde error controlado y se limpia el
  temporal si se excede). Sondeo de estado desde el frontend: cada 1,5 s.
- **Rationale**: Cumple la regla de la constitución de no leer un fichero
  ilimitado completo en memoria y deja margen razonable sobre el objetivo de
  rendimiento antes de considerarlo un fallo, sin bloquear indefinidamente al
  usuario.
- **Alternatives considered**: Sin tiempo máximo (rechazado: contradice el
  requisito de errores claros ante fallos y el principio de Observabilidad de
  la constitución del proyecto raíz).

## 8. Prueba de escucha (SC-003 / constitución sección "Voz natural")

- **Decision**: Conjunto de frases de prueba en español que incluyen números
  (enteros, decimales con coma, fechas) y siglas comunes (ONU, ADN, FAQ, ej.
  "la OMS informó que el 23,5% de 1.024 casos..."), narradas con
  `es_ES-davefx-medium` y evaluadas manualmente por al menos un oyente con el
  criterio de SC-003 (≥90% de palabras identificadas correctamente). El
  resultado (fecha, oyente, porcentaje, observaciones) se registrará en una
  sección "Resultados de la prueba de escucha" de este `plan.md` antes de
  publicar, como exige la constitución.
- **Rationale**: Reutiliza directamente el criterio ya definido en `spec.md`
  sin introducir un nuevo umbral; mantiene la prueba manual y ligera acorde al
  alcance de esta iteración.
- **Estado**: Pendiente de ejecutar — bloqueante solo para la publicación, no
  para continuar con `/speckit-tasks` e implementación (ver spec.md
  Assumptions).
