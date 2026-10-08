"""Punto de entrada de la aplicación FastAPI (data-model.md, contracts/api.md)."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lector_documentos.api import documents
from lector_documentos.api.errors import registrar_manejadores_de_error
from lector_documentos.services.cleanup import iniciar_barrido_de_expirados
from lector_documentos.services.job_store import almacen_de_trabajos
from lector_documentos.services.tts import verificar_motor_disponible

# Formato estructurado (marca de tiempo, nivel, logger, mensaje). Invariante
# de la aplicación (FR-032): ningún `logger.*` de este proyecto recibe nunca
# el contenido de un documento ni credenciales como argumento; solo
# identificadores de trabajo (`job_id`) y metadatos no sensibles.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("lector_documentos.main")

ENGINE_DISPONIBLE_KEY = "piper_disponible"

# Métodos y cabeceras permitidos por CORS (FR-037, contracts/api.md
# "Comunicación entre orígenes distintos (CORS)"). CORS es una restricción
# del navegador, no un mecanismo de autorización del servidor: cada endpoint
# sigue revalidando sus propias reglas (formato, tamaño, sesión) con
# independencia del origen filtrado por CORS.
METODOS_CORS_PERMITIDOS = ["GET", "POST", "DELETE", "OPTIONS"]
CABECERAS_CORS_PERMITIDAS = ["Content-Type", "X-Session-Token"]


def _origenes_permitidos() -> list[str]:
    """Lee `ALLOWED_ORIGINS` (lista separada por comas) del entorno del
    backend. Sin valores fijos en código (FR-036): cada entorno define sus
    propios orígenes de frontend autorizados. Si la variable falta o está
    vacía, no se permite ningún origen (fail-closed)."""
    valor = os.environ.get("ALLOWED_ORIGINS", "")
    return [origen.strip() for origen in valor.split(",") if origen.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chequeo de arranque: verifica que Piper y el modelo de voz son cargables
    # (alimenta el caso 503 de contracts/api.md). No registra contenido de
    # documentos ni credenciales (FR-032).
    disponible = verificar_motor_disponible()
    app.state.piper_disponible = disponible
    if disponible:
        logger.info("Motor Piper y modelo de voz cargados correctamente.")
    else:
        logger.warning("Motor Piper o modelo de voz NO disponibles al arrancar.")

    # Barrido periódico de temporales expirados (SC-005, FR-030).
    detener_barrido = iniciar_barrido_de_expirados(almacen_de_trabajos)
    try:
        yield
    finally:
        detener_barrido.set()


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Lector de Documentos con Voz",
        description="API para subir documentos Markdown en español y narrarlos con Piper.",
        lifespan=lifespan,
    )
    registrar_manejadores_de_error(app)
    # CORS (FR-034, FR-035, FR-037): el frontend llama al backend desde un
    # origen distinto en todo entorno, nunca mediante un proxy. Nunca se usa
    # `*` junto con cabeceras sensibles como `X-Session-Token`.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origenes_permitidos(),
        allow_methods=METODOS_CORS_PERMITIDOS,
        allow_headers=CABECERAS_CORS_PERMITIDAS,
    )
    app.include_router(documents.router, prefix="/api")
    return app


app = crear_app()
