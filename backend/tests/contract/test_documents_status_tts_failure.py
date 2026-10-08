"""T049: contract test — si Piper/el modelo no están disponibles,
GET /api/documents/{job_id}/status devuelve 503 sin recurrir a un proveedor
alternativo (FR-019)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from lector_documentos.main import app


def test_status_motor_no_disponible_devuelve_503() -> None:
    with TestClient(app) as client:
        app.state.piper_disponible = False
        try:
            respuesta = client.get("/api/documents/cualquier-job-id/status")
        finally:
            app.state.piper_disponible = True

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "motor_no_disponible"
