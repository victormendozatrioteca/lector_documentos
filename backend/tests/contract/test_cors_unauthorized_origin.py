"""T067: contract test — CORS rechaza un origen no autorizado (FR-037,
SC-010, contracts/api.md "Comunicación entre orígenes distintos (CORS)").

Una petición cuyo encabezado `Origin` NO está en `ALLOWED_ORIGINS` no debe
recibir `Access-Control-Allow-Origin`. Además, el backend debe seguir
validando el cuerpo de la petición de forma independiente al resultado de
CORS: CORS es una restricción del navegador, no un mecanismo de autorización
del servidor.
"""

from __future__ import annotations

import importlib
import io

from fastapi.testclient import TestClient

ORIGEN_AUTORIZADO = "http://localhost:5173"
ORIGEN_NO_AUTORIZADO = "http://evil.example.com"


def _crear_cliente_con_origenes(monkeypatch, origenes: str) -> TestClient:
    monkeypatch.setenv("ALLOWED_ORIGINS", origenes)
    from lector_documentos import main as modulo_main

    importlib.reload(modulo_main)
    return TestClient(modulo_main.app)


def test_origen_no_autorizado_no_recibe_access_control_allow_origin(monkeypatch) -> None:
    with _crear_cliente_con_origenes(monkeypatch, ORIGEN_AUTORIZADO) as client:
        respuesta = client.get(
            "/api/documents/un-job-inexistente/status",
            headers={"Origin": ORIGEN_NO_AUTORIZADO},
        )

    assert "access-control-allow-origin" not in {
        clave.lower() for clave in respuesta.headers.keys()
    }


def test_backend_sigue_validando_el_cuerpo_pese_a_origen_no_autorizado(monkeypatch) -> None:
    """CORS no sustituye la validación del backend (FR-037): un archivo con
    formato incorrecto debe seguir siendo rechazado con 4xx aunque la
    petición provenga de un origen no autorizado y el navegador fuera a
    bloquear la lectura de la respuesta igualmente."""
    with _crear_cliente_con_origenes(monkeypatch, ORIGEN_AUTORIZADO) as client:
        respuesta = client.post(
            "/api/documents",
            headers={"Origin": ORIGEN_NO_AUTORIZADO},
            files={
                "file": (
                    "prueba.txt",
                    io.BytesIO(b"contenido no markdown"),
                    "text/plain",
                )
            },
        )

    assert respuesta.status_code >= 400
    assert "access-control-allow-origin" not in {
        clave.lower() for clave in respuesta.headers.keys()
    }
