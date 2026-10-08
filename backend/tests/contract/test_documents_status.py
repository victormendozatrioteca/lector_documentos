"""T015: contract test — GET /api/documents/{job_id}/status, transiciones
(contracts/api.md)."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

from lector_documentos.main import app


def test_status_transita_de_cargando_a_listo() -> None:
    contenido = "# Título\n\nUn párrafo en español con contenido narrable.\n"
    with TestClient(app) as client:
        subida = client.post(
            "/api/documents",
            files={"file": ("prueba.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
        )
        job_id = subida.json()["job_id"]

        estados_observados = []
        for _ in range(60):
            respuesta = client.get(f"/api/documents/{job_id}/status")
            assert respuesta.status_code == 200
            cuerpo = respuesta.json()
            estados_observados.append(cuerpo["estado_procesamiento"])
            if cuerpo["estado_procesamiento"] in ("listo", "error"):
                break
            time.sleep(0.1)

        assert estados_observados[-1] == "listo"
        assert cuerpo["duracion_segundos"] is not None
        assert cuerpo["duracion_segundos"] > 0


def test_status_de_job_id_desconocido_devuelve_404() -> None:
    with TestClient(app) as client:
        respuesta = client.get("/api/documents/00000000-0000-0000-0000-000000000000/status")
    assert respuesta.status_code == 404
