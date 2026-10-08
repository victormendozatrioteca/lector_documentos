"""Almacén de trabajos en memoria (data-model.md §1, research.md §6).

Aplica la regla: un único trabajo activo por ``session_token``. Si llega un
nuevo trabajo para la misma sesión mientras el anterior está en
``procesando``, el anterior se cancela cooperativamente (FR-031a) antes de
registrar el nuevo.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from lector_documentos.models.schemas import (
    AudioNarrado,
    Documento,
    EstadoAudio,
    EstadoProcesamiento,
    EstadoValidacion,
)

ESTADOS_TERMINALES = {
    EstadoProcesamiento.LISTO,
    EstadoProcesamiento.ERROR,
    EstadoProcesamiento.CANCELADO,
}

ESTADOS_EN_VUELO = {EstadoProcesamiento.CARGANDO, EstadoProcesamiento.PROCESANDO}


@dataclass
class Trabajo:
    """Agrupa el ``Documento`` y su ``AudioNarrado`` asociado (relación 1:1)."""

    documento: Documento
    audio: AudioNarrado
    cancelado: threading.Event = field(default_factory=threading.Event)


class AlmacenDeTrabajos:
    """Almacén thread-safe de trabajos, indexado por ``job_id`` y por sesión."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._trabajos: dict[str, Trabajo] = {}
        self._trabajo_activo_por_sesion: dict[str, str] = {}

    def generar_job_id(self) -> str:
        return str(uuid.uuid4())

    def generar_session_token(self) -> str:
        return str(uuid.uuid4())

    def crear_trabajo(
        self,
        session_token: str,
        nombre_archivo: str,
        tamano_bytes: int,
        ruta_temporal: str,
    ) -> Trabajo:
        """Crea un nuevo trabajo, cancelando el anterior de la misma sesión si
        sigue en vuelo (FR-031a)."""

        with self._lock:
            anterior_id = self._trabajo_activo_por_sesion.get(session_token)
            if anterior_id is not None:
                anterior = self._trabajos.get(anterior_id)
                if anterior is not None and anterior.documento.estado_procesamiento in (
                    ESTADOS_EN_VUELO
                ):
                    anterior.cancelado.set()
                    anterior.documento.estado_procesamiento = EstadoProcesamiento.CANCELADO

            job_id = self.generar_job_id()
            documento = Documento(
                job_id=job_id,
                session_token=session_token,
                nombre_archivo=nombre_archivo,
                tamano_bytes=tamano_bytes,
                codificacion_valida=True,
                idioma_valido=True,
                tiene_contenido_narrable=True,
                estado_validacion=EstadoValidacion.VALIDO,
                motivo_rechazo=None,
                estado_procesamiento=EstadoProcesamiento.CARGANDO,
                ruta_temporal=ruta_temporal,
                creado_en=datetime.now(UTC),
            )
            audio = AudioNarrado(job_id=job_id, estado=EstadoAudio.GENERANDO)
            trabajo = Trabajo(documento=documento, audio=audio)
            self._trabajos[job_id] = trabajo
            self._trabajo_activo_por_sesion[session_token] = job_id
            return trabajo

    def obtener(self, job_id: str) -> Trabajo | None:
        with self._lock:
            return self._trabajos.get(job_id)

    def eliminar(self, job_id: str) -> Trabajo | None:
        with self._lock:
            trabajo = self._trabajos.pop(job_id, None)
            if trabajo is not None:
                sesion = trabajo.documento.session_token
                if self._trabajo_activo_por_sesion.get(sesion) == job_id:
                    del self._trabajo_activo_por_sesion[sesion]
            return trabajo

    def listar_expirables(self, limite: datetime) -> list[Trabajo]:
        with self._lock:
            return [
                t
                for t in self._trabajos.values()
                if t.documento.estado_procesamiento in ESTADOS_TERMINALES
                and t.documento.creado_en <= limite
            ]


almacen_de_trabajos = AlmacenDeTrabajos()
"""Instancia única de proceso (uso bajo/personal, 1-5 usuarios; research.md §6)."""
