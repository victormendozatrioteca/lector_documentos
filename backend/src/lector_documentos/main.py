"""Punto de entrada de la aplicación FastAPI (data-model.md, contracts/api.md)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    app.include_router(documents.router, prefix="/api")
    return app


app = crear_app()
