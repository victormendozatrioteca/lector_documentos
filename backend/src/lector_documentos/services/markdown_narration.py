"""Conversión de Markdown a texto narrable (FR-008..FR-014, constitución §3).

Usa `markdown-it-py` para obtener el flujo de tokens (sin ejecutar ni
renderizar HTML, sin descargar recursos enlazados) y extrae únicamente el
texto narrable en el mismo orden del documento, respetando las reglas:

- Encabezados, párrafos, citas y elementos de lista: un bloque narrable por
  cada uno, con una pausa perceptible entre bloques (FR-008).
- No se pronuncian los marcadores de formato Markdown (FR-009): se extrae el
  texto ya "renderizado" de cada token `inline`, nunca la sintaxis cruda.
- Enlaces: se narra el texto visible, nunca la URL (FR-010).
- Imágenes: se narra solo el texto alternativo si existe; si no existe, no se
  narra nada (FR-011).
- Tablas: dado que `markdown-it-py` emite los tokens de celda en orden
  encabezados→filas, izquierda a derecha, tratar cada celda como su propio
  bloque narrable reproduce exactamente esa regla, con pausa entre celdas
  (FR-012).
- Se omiten: código en línea, bloques de código, líneas separadoras, HTML
  crudo (no se generan tokens `inline` para ellos) y URLs aisladas (un bloque
  cuyo texto completo es una URL) (FR-013, FR-014).
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

_PARSER = MarkdownIt("commonmark", {"html": True}).enable("table")

_PATRON_URL_AISLADA = re.compile(r"^(?:https?|ftp)://\S+$", re.IGNORECASE)

# Tipos de token hijo (dentro de un token `inline`) que aportan texto narrable.
_TIPOS_TEXTO = {"text", "image"}
_TIPOS_SALTO_DE_LINEA = {"softbreak", "hardbreak"}
# Tipos que se omiten explícitamente: código en línea y HTML crudo (FR-013, FR-014).
_TIPOS_OMITIDOS = {"code_inline", "html_inline"}


def _texto_de_inline(token: Token) -> str:
    """Extrae el texto narrable de un token `inline`, aplicando las reglas de
    enlaces (solo texto visible), imágenes (solo alt) y omisiones."""

    partes: list[str] = []
    for hijo in token.children or []:
        if hijo.type == "image":
            if hijo.content:
                partes.append(hijo.content)
        elif hijo.type == "text":
            partes.append(hijo.content)
        elif hijo.type in _TIPOS_SALTO_DE_LINEA:
            partes.append(" ")
        elif hijo.type in _TIPOS_OMITIDOS:
            continue
        # link_open/link_close, strong_open/close, em_open/close, etc. son solo
        # marcadores sin contenido propio: el texto visible ya llega como un
        # token `text` independiente entre ellos (FR-009, FR-010).

    return "".join(partes).strip()


def generar_bloques_narrables(markdown_texto: str) -> list[str]:
    """Devuelve la lista ordenada de bloques narrables de un documento
    Markdown, uno por cada encabezado/párrafo/elemento de lista/celda de
    tabla con contenido, listos para sintetizarse con una pausa entre cada
    uno (FR-008..FR-014)."""

    tokens = _PARSER.parse(markdown_texto)
    bloques: list[str] = []

    for token in tokens:
        if token.type != "inline":
            continue

        texto = _texto_de_inline(token)
        if not texto:
            continue
        if _PATRON_URL_AISLADA.match(texto):
            # URL aislada: se omite por completo (FR-013).
            continue

        bloques.append(texto)

    return bloques


def tiene_contenido_narrable(markdown_texto: str) -> bool:
    """Usado por la validación (FR-004): ``False`` si, tras aplicar las
    reglas de omisión, no queda ningún texto narrable."""

    return len(generar_bloques_narrables(markdown_texto)) > 0
