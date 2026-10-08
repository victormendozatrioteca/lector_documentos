"""T046: contract test — subir un archivo que no es .md devuelve 415 con
codigo "formato_incorrecto" (FR-002)."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from lector_documentos.main import app


def test_post_documents_formato_incorrecto_devuelve_415() -> None:
    contenido = "Contenido cualquiera."
    with TestClient(app) as client:
        respuesta = client.post(
            "/api/documents",
            files={"file": ("prueba.txt", io.BytesIO(contenido.encode("utf-8")), "text/plain")},
        )

    assert respuesta.status_code == 415
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "formato_incorrecto"
