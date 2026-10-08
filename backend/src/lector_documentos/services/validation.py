"""Validación de documentos subidos (FR-002, FR-003, FR-004, FR-007,
constitución §5): formato, codificación, idioma, tamaño y contenido
narrable, comprobados en el backend aunque el navegador ya los haya
verificado."""

from __future__ import annotations

import re

from fastapi import UploadFile

from lector_documentos.api.errors import ErrorDominio
from lector_documentos.models.schemas import TAMANO_MAXIMO_BYTES
from lector_documentos.services.markdown_narration import tiene_contenido_narrable

_EXTENSION_VALIDA = ".md"

# Heurística simple y determinista de "contenido en español": exige la
# presencia de al menos una palabra común en español o un carácter propio del
# idioma (vocal acentuada, ñ); evita falsos negativos en documentos cortos
# sin imponer un detector de idioma pesado, acorde al alcance de esta
# iteración (FR-002, FR-007).
_PATRON_SENAL_ESPANOL = re.compile(
    r"[áéíóúñÁÉÍÓÚÑ¿¡]|\b(el|la|los|las|de|que|y|en|un|una|es|por|con|para|se|su)\b",
    re.IGNORECASE,
)


def validar_extension(nombre_archivo: str) -> None:
    if not nombre_archivo.lower().endswith(_EXTENSION_VALIDA):
        raise ErrorDominio(
            415,
            "formato_incorrecto",
            "Solo se admiten archivos Markdown (.md).",
        )


async def leer_con_limite_de_tamano(file: UploadFile) -> bytes:
    """Lee el archivo en streaming, cortando en cuanto se supera
    ``TAMANO_MAXIMO_BYTES`` sin acumular un fichero ilimitado completo en
    memoria (FR-003, constitución §5)."""

    fragmentos: list[bytes] = []
    total = 0
    tamano_bloque = 1024 * 64

    while True:
        bloque = await file.read(tamano_bloque)
        if not bloque:
            break
        total += len(bloque)
        if total > TAMANO_MAXIMO_BYTES:
            raise ErrorDominio(
                413,
                "tamano_excedido",
                "El archivo supera el tamaño máximo permitido de 5 MB.",
            )
        fragmentos.append(bloque)

    return b"".join(fragmentos)


def validar_codificacion_utf8(contenido_bytes: bytes) -> str:
    try:
        return contenido_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ErrorDominio(
            415,
            "formato_incorrecto",
            "El archivo debe estar codificado en UTF-8.",
        ) from exc


def validar_idioma_espanol(texto: str) -> None:
    if not _PATRON_SENAL_ESPANOL.search(texto):
        raise ErrorDominio(
            422,
            "idioma_no_valido",
            "El documento no parece contener texto en español.",
        )


def validar_contenido_narrable(texto: str) -> None:
    if not texto.strip() or not tiene_contenido_narrable(texto):
        raise ErrorDominio(
            422,
            "sin_contenido_narrable",
            "El documento está vacío o no tiene contenido que se pueda narrar.",
        )
