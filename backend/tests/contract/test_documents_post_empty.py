"""T048: contract test — un .md vacío o sin contenido narrable devuelve 422
con codigo "sin_contenido_narrable" (FR-004)."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from lector_documentos.main import app


def test_post_documents_vacio_devuelve_422_sin_contenido_narrable() -> None:
    with TestClient(app) as client:
        respuesta = client.post(
            "/api/documents",
            files={"file": ("vacio.md", io.BytesIO(b""), "text/markdown")},
        )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "sin_contenido_narrable"


def test_post_documents_solo_codigo_devuelve_422_sin_contenido_narrable() -> None:
    # Palabras en español dentro de un bloque de código: supera la detección
    # de idioma, pero no aporta contenido narrable porque el código se omite.
    contenido = "```\nel la los las de que y en un una es por con para se su\n```\n"
    with TestClient(app) as client:
        respuesta = client.post(
            "/api/documents",
            files={
                "file": (
                    "solo_codigo.md",
                    io.BytesIO(contenido.encode("utf-8")),
                    "text/markdown",
                )
            },
        )

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "sin_contenido_narrable"
