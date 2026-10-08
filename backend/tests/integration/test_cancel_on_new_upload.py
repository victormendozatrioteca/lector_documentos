"""T018: integration test — subir un segundo documento de la misma sesión
cancela el trabajo anterior y limpia sus temporales (FR-031a)."""

from __future__ import annotations

import io
import time
from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

from lector_documentos.main import app
from lector_documentos.services.job_store import almacen_de_trabajos


def test_nueva_subida_misma_sesion_cancela_trabajo_anterior() -> None:
    contenido_largo = "# Título\n\n" + ("Párrafo largo para narrar. " * 200) + "\n"
    contenido_corto = "# Otro\n\nUn párrafo corto.\n"

    with TestClient(app) as client:
        primera = client.post(
            "/api/documents",
            files={
                "file": (
                    "largo.md",
                    io.BytesIO(contenido_largo.encode("utf-8")),
                    "text/markdown",
                )
            },
        )
        assert primera.status_code == 202
        primer_job_id = primera.json()["job_id"]
        session_token = primera.json()["session_token"]

        segunda = client.post(
            "/api/documents",
            files={
                "file": (
                    "corto.md",
                    io.BytesIO(contenido_corto.encode("utf-8")),
                    "text/markdown",
                )
            },
            headers={"X-Session-Token": session_token},
        )
        assert segunda.status_code == 202
        segundo_job_id = segunda.json()["job_id"]

        # Esperar (con sondeo) a que la cancelación y limpieza del primer
        # trabajo se reflejen; la síntesis del primer trabajo puede tardar
        # varios segundos en notar la cancelación entre bloques.
        primer_trabajo = None
        for _ in range(100):
            primer_trabajo = almacen_de_trabajos.obtener(primer_job_id)
            if (
                primer_trabajo is not None
                and primer_trabajo.documento.estado_procesamiento == "cancelado"
            ):
                break
            time.sleep(0.1)

    assert primer_trabajo is not None
    assert primer_trabajo.documento.estado_procesamiento == "cancelado"
    assert segundo_job_id != primer_job_id

    directorio_primer_trabajo = Path(gettempdir()) / "lector_documentos_jobs" / primer_job_id
    for _ in range(200):
        if (
            not directorio_primer_trabajo.exists()
            or list(directorio_primer_trabajo.iterdir()) == []
        ):
            break
        time.sleep(0.1)
    assert not directorio_primer_trabajo.exists() or list(directorio_primer_trabajo.iterdir()) == []
