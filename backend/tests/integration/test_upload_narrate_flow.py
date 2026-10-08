"""T017: integration test — flujo completo upload→poll→listo dentro del
objetivo SC-001 (< 60 s) para un documento válido en español."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

from lector_documentos.main import app

SC001_LIMITE_SEGUNDOS = 60


def test_flujo_completo_upload_poll_listo_dentro_de_60s() -> None:
    contenido = (
        "# Documento de prueba\n\n"
        "Este es el primer párrafo narrable en español.\n\n"
        "Este es el segundo párrafo, con más contenido para narrar.\n\n"
        "- Primer elemento de lista\n- Segundo elemento de lista\n\n"
        "> Una cita breve para verificar el orden de narración.\n"
    )

    inicio = time.monotonic()
    with TestClient(app) as client:
        subida = client.post(
            "/api/documents",
            files={"file": ("prueba.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
        )
        assert subida.status_code == 202
        job_id = subida.json()["job_id"]

        estado_final = None
        while time.monotonic() - inicio < SC001_LIMITE_SEGUNDOS:
            estado = client.get(f"/api/documents/{job_id}/status").json()
            if estado["estado_procesamiento"] in ("listo", "error"):
                estado_final = estado
                break
            time.sleep(0.1)

        transcurrido = time.monotonic() - inicio

    assert estado_final is not None, "El trabajo no alcanzó un estado terminal a tiempo"
    assert estado_final["estado_procesamiento"] == "listo"
    assert transcurrido < SC001_LIMITE_SEGUNDOS
