"""Tubería de procesamiento secuencial: validar → parsear → narrar →
sintetizar → listo (FR-007a: una sola síntesis en vuelo a la vez)."""

from __future__ import annotations

import logging
import threading

from lector_documentos.models.schemas import EstadoAudio, EstadoProcesamiento
from lector_documentos.services import cleanup
from lector_documentos.services.job_store import Trabajo
from lector_documentos.services.markdown_narration import generar_bloques_narrables
from lector_documentos.services.tts import (
    MotorNoDisponibleError,
    SintesisCanceladaError,
    SintesisFallidaError,
    sintetizar_bloques_a_wav,
)

logger = logging.getLogger("lector_documentos.pipeline")

# Un único lock de proceso garantiza que haya como máximo una síntesis Piper
# en vuelo a la vez, suficiente para el volumen de 1-5 usuarios (FR-007a,
# research.md §5/§6).
_lock_sintesis = threading.Lock()


def procesar_trabajo(trabajo: Trabajo, contenido_markdown: str) -> None:
    """Ejecuta el pipeline completo para un trabajo ya validado y aceptado.
    Pensado para ejecutarse en un hilo en segundo plano, iniciado por el
    endpoint `POST /api/documents`."""

    documento = trabajo.documento
    audio = trabajo.audio

    if trabajo.cancelado.is_set():
        return

    documento.estado_procesamiento = EstadoProcesamiento.PROCESANDO

    try:
        bloques = generar_bloques_narrables(contenido_markdown)

        if trabajo.cancelado.is_set():
            return

        directorio = cleanup.directorio_de_trabajo(documento.job_id)
        ruta_audio = directorio / "audio.wav"

        with _lock_sintesis:
            if trabajo.cancelado.is_set():
                return
            duracion = sintetizar_bloques_a_wav(
                bloques, ruta_audio, debe_cancelar=trabajo.cancelado.is_set
            )

        if trabajo.cancelado.is_set():
            cleanup.limpiar_trabajo(documento.job_id)
            return

        audio.ruta_temporal = str(ruta_audio)
        audio.duracion_segundos = duracion
        audio.estado = EstadoAudio.LISTO
        documento.estado_procesamiento = EstadoProcesamiento.LISTO

    except MotorNoDisponibleError as exc:
        audio.estado = EstadoAudio.ERROR
        audio.motivo_error = str(exc)
        documento.estado_procesamiento = EstadoProcesamiento.ERROR
    except SintesisCanceladaError:
        cleanup.limpiar_trabajo(documento.job_id)
    except SintesisFallidaError as exc:
        audio.estado = EstadoAudio.ERROR
        audio.motivo_error = str(exc)
        documento.estado_procesamiento = EstadoProcesamiento.ERROR
    except Exception:  # pragma: no cover - salvaguarda genérica
        logger.exception("Fallo inesperado al procesar job_id=%s", documento.job_id)
        audio.estado = EstadoAudio.ERROR
        audio.motivo_error = "Fallo interno inesperado."
        documento.estado_procesamiento = EstadoProcesamiento.ERROR


def iniciar_procesamiento_en_segundo_plano(trabajo: Trabajo, contenido_markdown: str) -> None:
    hilo = threading.Thread(
        target=procesar_trabajo,
        args=(trabajo, contenido_markdown),
        daemon=True,
    )
    hilo.start()
