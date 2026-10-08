"""Endpoints de documentos (contracts/api.md)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Header, Request, UploadFile
from fastapi.responses import FileResponse

from lector_documentos.api.errors import ErrorDominio
from lector_documentos.models.schemas import (
    DocumentoAceptadoRespuesta,
    ErrorDetalle,
    EstadoProcesamiento,
    EstadoRespuesta,
)
from lector_documentos.services import cleanup, validation
from lector_documentos.services.job_store import almacen_de_trabajos
from lector_documentos.services.pipeline import iniciar_procesamiento_en_segundo_plano

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=202, response_model=DocumentoAceptadoRespuesta)
async def subir_documento(
    request: Request,
    file: UploadFile,
    x_session_token: str | None = Header(default=None),
) -> DocumentoAceptadoRespuesta:
    if not request.app.state.piper_disponible:
        raise ErrorDominio(
            503,
            "motor_no_disponible",
            "El motor de síntesis de voz no está disponible en este momento.",
        )

    nombre_archivo = file.filename or "documento.md"
    validation.validar_extension(nombre_archivo)

    contenido_bytes = await validation.leer_con_limite_de_tamano(file)
    texto = validation.validar_codificacion_utf8(contenido_bytes)
    validation.validar_contenido_narrable(texto)
    validation.validar_idioma_espanol(texto)

    session_token = x_session_token or str(uuid.uuid4())

    trabajo = almacen_de_trabajos.crear_trabajo(
        session_token=session_token,
        nombre_archivo=nombre_archivo,
        tamano_bytes=len(contenido_bytes),
        ruta_temporal="",
    )

    directorio = cleanup.directorio_de_trabajo(trabajo.documento.job_id)
    ruta_original = directorio / nombre_archivo
    ruta_original.write_bytes(contenido_bytes)
    trabajo.documento.ruta_temporal = str(ruta_original)

    iniciar_procesamiento_en_segundo_plano(trabajo, texto)

    return DocumentoAceptadoRespuesta(
        job_id=trabajo.documento.job_id,
        session_token=session_token,
        nombre_archivo=nombre_archivo,
        estado_procesamiento=EstadoProcesamiento.CARGANDO,
    )


@router.get("/{job_id}/status", response_model=EstadoRespuesta)
async def obtener_estado(request: Request, job_id: str) -> EstadoRespuesta:
    if not request.app.state.piper_disponible:
        raise ErrorDominio(
            503,
            "motor_no_disponible",
            "El motor de síntesis de voz no está disponible en este momento.",
        )

    trabajo = almacen_de_trabajos.obtener(job_id)
    if trabajo is None:
        raise ErrorDominio(404, "trabajo_no_encontrado", "El documento solicitado no existe.")

    documento = trabajo.documento
    audio = trabajo.audio

    error_detalle = None
    if documento.estado_procesamiento == "error" and audio.motivo_error:
        error_detalle = ErrorDetalle(
            codigo="fallo_sintesis",
            mensaje="No se pudo generar el audio para este documento.",
        )

    return EstadoRespuesta(
        job_id=documento.job_id,
        nombre_archivo=documento.nombre_archivo,
        estado_procesamiento=documento.estado_procesamiento,
        duracion_segundos=audio.duracion_segundos,
        error=error_detalle,
    )


@router.get("/{job_id}/audio")
async def obtener_audio(job_id: str) -> FileResponse:
    trabajo = almacen_de_trabajos.obtener(job_id)
    if trabajo is None:
        raise ErrorDominio(404, "trabajo_no_encontrado", "El documento solicitado no existe.")

    documento = trabajo.documento
    audio = trabajo.audio

    if documento.estado_procesamiento == "error":
        raise ErrorDominio(
            500, "fallo_sintesis", "No se pudo generar el audio para este documento."
        )

    if documento.estado_procesamiento != "listo" or not audio.ruta_temporal:
        raise ErrorDominio(
            409,
            "audio_no_listo",
            "El audio todavía se está generando. Inténtalo en unos segundos.",
        )

    return FileResponse(audio.ruta_temporal, media_type="audio/wav")


@router.delete("/{job_id}", status_code=204)
async def cancelar_documento(job_id: str) -> None:
    trabajo = almacen_de_trabajos.obtener(job_id)
    if trabajo is not None:
        trabajo.cancelado.set()
        almacen_de_trabajos.eliminar(job_id)
        cleanup.limpiar_trabajo(job_id)
