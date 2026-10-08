# Lector de Documentos con Voz — Backend

API FastAPI que recibe documentos Markdown en español, los narra y genera el
audio con [Piper](https://github.com/OHF-voice/piper1-gpl) (modelo
`es_ES-davefx-medium`) de forma local, sin enviar el contenido a ningún
proveedor externo.

## Requisitos

- Python 3.12
- [`uv`](https://docs.astral.sh/uv/)
- Modelo de voz Piper descargado en `backend/models/`:
  - `es_ES-davefx-medium.onnx`
  - `es_ES-davefx-medium.onnx.json`

## Instalación

```bash
cd backend
uv sync
```

## Ejecutar el servidor

```bash
uv run uvicorn lector_documentos.main:app --reload
```

## CORS: orígenes del frontend autorizados

El frontend se sirve desde un origen distinto al del backend, sin proxy
(FR-034, FR-035). Antes de arrancar, define `ALLOWED_ORIGINS` con la lista de
orígenes de frontend autorizados (separados por comas, sin espacios, sin
valores fijos en el código — FR-036/FR-037):

```bash
export ALLOWED_ORIGINS="http://localhost:5173"
# varios orígenes: "https://app.ejemplo.com,http://localhost:5173"
```

Si `ALLOWED_ORIGINS` falta o está vacía, no se permite ningún origen
(fail-closed). CORS solo controla qué orígenes puede leer el navegador; cada
endpoint sigue validando sus propias reglas (formato, tamaño, sesión) con
independencia del origen de la petición.


## Comandos de control de calidad

Ejecutar antes de cada commit o pull request:

```bash
uv run pytest                      # Pruebas (contrato, integración, unitarias)
uv run ruff check .                # Lint
uv run ruff format --check .       # Formato (sin aplicar cambios)
uv run mypy .                      # Tipado estático
```

Para aplicar automáticamente el formato:

```bash
uv run ruff format .
```

## Privacidad y datos temporales

- Los documentos y audios se almacenan únicamente en un directorio temporal
  por trabajo, limpiado al finalizar, fallar, cancelar un trabajo, o tras un
  barrido periódico de expiración (5 minutos).
- Los registros (logging) nunca incluyen el contenido de los documentos ni
  credenciales; solo identificadores de trabajo (`job_id`) y metadatos no
  sensibles (FR-032).

## Licencias

- Piper y sus voces se distribuyen bajo licencia **GPL-3.0**. Antes de
  redistribuir este backend junto con los pesos del modelo, confirmar la
  licencia específica de `es_ES-davefx-medium` y cumplir las obligaciones de
  la GPL-3.0 (ver `specs/001-voice-document-reader/plan.md`).
