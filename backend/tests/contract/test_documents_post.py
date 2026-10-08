"""T014: contract test — POST /api/documents, caso feliz (contracts/api.md)."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from lector_documentos.main import app


def test_post_documents_happy_path_devuelve_202_con_job_id() -> None:
    contenido = "# Título\n\nUn párrafo en español con contenido narrable.\n"
    with TestClient(app) as client:
        respuesta = client.post(
            "/api/documents",
            files={"file": ("prueba.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
        )

    assert respuesta.status_code == 202
    cuerpo = respuesta.json()
    assert "job_id" in cuerpo
    assert "session_token" in cuerpo
    assert cuerpo["nombre_archivo"] == "prueba.md"
    assert cuerpo["estado_procesamiento"] == "cargando"
