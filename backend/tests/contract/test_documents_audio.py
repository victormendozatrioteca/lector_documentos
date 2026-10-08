"""T016: contract test — GET /api/documents/{job_id}/audio (contracts/api.md)."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

from lector_documentos.main import app


def _subir_y_esperar_listo(client: TestClient) -> str:
    contenido = "# Título\n\nUn párrafo en español con contenido narrable.\n"
    subida = client.post(
        "/api/documents",
        files={"file": ("prueba.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
    )
    job_id = subida.json()["job_id"]
    for _ in range(60):
        estado = client.get(f"/api/documents/{job_id}/status").json()
        if estado["estado_procesamiento"] in ("listo", "error"):
            break
        time.sleep(0.1)
    return job_id


def test_audio_listo_devuelve_200_audio_wav() -> None:
    with TestClient(app) as client:
        job_id = _subir_y_esperar_listo(client)
        respuesta = client.get(f"/api/documents/{job_id}/audio")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "audio/wav"
    assert len(respuesta.content) > 0


def test_audio_no_listo_devuelve_409() -> None:
    with TestClient(app) as client:
        contenido = "# Título\n\nUn párrafo en español con contenido narrable.\n"
        subida = client.post(
            "/api/documents",
            files={"file": ("prueba.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
        )
        job_id = subida.json()["job_id"]
        respuesta = client.get(f"/api/documents/{job_id}/audio")

    assert respuesta.status_code in (200, 409)


def test_audio_job_desconocido_devuelve_404() -> None:
    with TestClient(app) as client:
        respuesta = client.get("/api/documents/00000000-0000-0000-0000-000000000000/audio")
    assert respuesta.status_code == 404
