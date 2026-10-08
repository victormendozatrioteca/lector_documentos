"""Esquema estándar de error y manejadores de excepciones FastAPI
(contracts/api.md): toda respuesta de error usa
``{ "error": { "codigo": "...", "mensaje": "..." } }`` y ``mensaje`` nunca
incluye trazas, rutas de archivo ni detalles internos (FR-033).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from lector_documentos.models.schemas import ErrorDetalle, ErrorRespuesta


class ErrorDominio(Exception):
    """Error de dominio con código HTTP y mensaje comprensible para el usuario."""

    def __init__(self, status_code: int, codigo: str, mensaje: str) -> None:
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje = mensaje
        super().__init__(mensaje)


def _error_response(status_code: int, codigo: str, mensaje: str) -> JSONResponse:
    body = ErrorRespuesta(error=ErrorDetalle(codigo=codigo, mensaje=mensaje))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def registrar_manejadores_de_error(app: FastAPI) -> None:
    """Registra los exception handlers globales de la aplicación."""

    @app.exception_handler(ErrorDominio)
    async def manejar_error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
        return _error_response(exc.status_code, exc.codigo, exc.mensaje)

    @app.exception_handler(HTTPException)
    async def manejar_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        # No exponer el detalle crudo de FastAPI/Starlette; usar un mensaje genérico
        # comprensible cuando el detalle no fue generado por nosotros mismos.
        mensaje = exc.detail if isinstance(exc.detail, str) else "Solicitud inválida."
        return _error_response(exc.status_code, "error_solicitud", mensaje)

    @app.exception_handler(Exception)
    async def manejar_error_interno(_: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            500,
            "error_interno",
            "Ocurrió un error interno al procesar el documento. Inténtalo de nuevo.",
        )
