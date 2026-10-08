"""Esquemas Pydantic para las entidades del dominio (data-model.md §1-2).

Todas las entidades son temporales: viven en memoria de proceso y/o en un
directorio temporal del sistema operativo durante el ciclo de vida de un
trabajo de narración (ver data-model.md).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

TAMANO_MAXIMO_BYTES = 5_000_000
"""Límite estricto de tamaño de archivo: 5 MB = 5.000.000 bytes (FR-003)."""


class EstadoValidacion(StrEnum):
    VALIDO = "valido"
    RECHAZADO = "rechazado"


class MotivoRechazo(StrEnum):
    FORMATO_INCORRECTO = "formato_incorrecto"
    TAMANO_EXCEDIDO = "tamano_excedido"
    VACIO_O_SIN_CONTENIDO_NARRABLE = "vacio_o_sin_contenido_narrable"
    CODIFICACION_INVALIDA = "codificacion_invalida"
    IDIOMA_NO_VALIDO = "idioma_no_valido"


class EstadoProcesamiento(StrEnum):
    CARGANDO = "cargando"
    PROCESANDO = "procesando"
    LISTO = "listo"
    ERROR = "error"
    CANCELADO = "cancelado"


class EstadoAudio(StrEnum):
    GENERANDO = "generando"
    LISTO = "listo"
    ERROR = "error"


class Documento(BaseModel):
    """Documento Markdown subido por el usuario (data-model.md §1)."""

    job_id: str
    session_token: str
    nombre_archivo: str
    tamano_bytes: int = Field(le=TAMANO_MAXIMO_BYTES)
    codificacion_valida: bool
    idioma_valido: bool
    tiene_contenido_narrable: bool
    estado_validacion: EstadoValidacion
    motivo_rechazo: MotivoRechazo | None = None
    estado_procesamiento: EstadoProcesamiento
    ruta_temporal: str
    creado_en: datetime


class AudioNarrado(BaseModel):
    """Resultado de la síntesis de voz asociado a un Documento (data-model.md §2)."""

    job_id: str
    ruta_temporal: str | None = None
    duracion_segundos: float | None = None
    estado: EstadoAudio
    motivo_error: str | None = None


class ErrorDetalle(BaseModel):
    """Cuerpo estándar de error de la API (contracts/api.md)."""

    codigo: str
    mensaje: str


class ErrorRespuesta(BaseModel):
    error: ErrorDetalle


class DocumentoAceptadoRespuesta(BaseModel):
    """Respuesta 202 de POST /api/documents."""

    job_id: str
    session_token: str
    nombre_archivo: str
    estado_procesamiento: EstadoProcesamiento


class EstadoRespuesta(BaseModel):
    """Respuesta 200 de GET /api/documents/{job_id}/status."""

    job_id: str
    nombre_archivo: str
    estado_procesamiento: EstadoProcesamiento
    duracion_segundos: float | None = None
    error: ErrorDetalle | None = None
