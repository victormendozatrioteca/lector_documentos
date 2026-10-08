"""Gestor de archivos temporales por trabajo (data-model.md §4, FR-006, FR-030, FR-031).

Cada trabajo obtiene su propio subdirectorio bajo un directorio temporal del
sistema operativo, distinto de ``backend/models/`` (recurso de aplicación de
larga duración, nunca limpiado por este módulo).
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lector_documentos.services.job_store import AlmacenDeTrabajos

logger = logging.getLogger("lector_documentos.cleanup")

SEGUNDOS_EXPIRACION = 5 * 60
"""Los temporales se eliminan 5 minutos tras finalizar la sesión (SC-005)."""

_RAIZ_TEMPORAL = Path(tempfile.gettempdir()) / "lector_documentos_jobs"


def directorio_de_trabajo(job_id: str) -> Path:
    """Crea (si no existe) y devuelve el directorio temporal exclusivo de un trabajo."""

    directorio = _RAIZ_TEMPORAL / job_id
    directorio.mkdir(parents=True, exist_ok=True)
    return directorio


def limpiar_trabajo(job_id: str) -> None:
    """Elimina el directorio temporal completo de un trabajo (fin, fallo, cancelación
    o pérdida de conexión, FR-030/FR-031). No registra el nombre del documento,
    solo el identificador de trabajo (FR-032)."""

    directorio = _RAIZ_TEMPORAL / job_id
    if directorio.exists():
        shutil.rmtree(directorio, ignore_errors=True)
        logger.info("temporales eliminados para job_id=%s", job_id)


def limpiar_expirados(trabajos_expirables: list[str]) -> None:
    """Elimina los temporales de trabajos en estado terminal con más de
    ``SEGUNDOS_EXPIRACION`` desde su creación (SC-005)."""

    for job_id in trabajos_expirables:
        limpiar_trabajo(job_id)


def limite_de_expiracion(ahora: datetime | None = None) -> datetime:
    referencia = ahora or datetime.now(UTC)
    return referencia - timedelta(seconds=SEGUNDOS_EXPIRACION)


INTERVALO_BARRIDO_SEGUNDOS = 60
"""Frecuencia del barrido periódico de trabajos expirados (SC-005)."""


def iniciar_barrido_de_expirados(
    almacen: AlmacenDeTrabajos,
    intervalo_segundos: int = INTERVALO_BARRIDO_SEGUNDOS,
) -> threading.Event:
    """Lanza un hilo en segundo plano que, cada ``intervalo_segundos``,
    elimina del almacén y del disco los trabajos terminales con más de
    ``SEGUNDOS_EXPIRACION`` de antigüedad (SC-005, FR-030). Devuelve un
    ``threading.Event`` que, al activarse (``.set()``), detiene el barrido
    (usado en el shutdown de la aplicación)."""

    detener = threading.Event()

    def _bucle() -> None:
        while not detener.wait(intervalo_segundos):
            limite = limite_de_expiracion()
            for trabajo in almacen.listar_expirables(limite):
                job_id = trabajo.documento.job_id
                almacen.eliminar(job_id)
                limpiar_trabajo(job_id)

    hilo = threading.Thread(target=_bucle, daemon=True, name="barrido-expirados")
    hilo.start()
    return detener
