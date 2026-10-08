"""T066: contract test — CORS permite un origen autorizado (FR-037,
contracts/api.md "Comunicación entre orígenes distintos (CORS)").

Una petición cuyo encabezado `Origin` está en `ALLOWED_ORIGINS` debe recibir
`Access-Control-Allow-Origin` para ese origen, y el preflight `OPTIONS` debe
responder correctamente con los métodos y cabeceras esperados.
"""

from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

ORIGEN_AUTORIZADO = "http://localhost:5173"


def _crear_cliente_con_origenes(monkeypatch, origenes: str) -> TestClient:
    monkeypatch.setenv("ALLOWED_ORIGINS", origenes)
    from lector_documentos import main as modulo_main

    importlib.reload(modulo_main)
    return TestClient(modulo_main.app)


def test_preflight_options_devuelve_cabeceras_cors_para_origen_autorizado(monkeypatch) -> None:
    with _crear_cliente_con_origenes(monkeypatch, ORIGEN_AUTORIZADO) as client:
        respuesta = client.options(
            "/api/documents",
            headers={
                "Origin": ORIGEN_AUTORIZADO,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type, x-session-token",
            },
        )

    assert respuesta.status_code == 200
    assert respuesta.headers.get("access-control-allow-origin") == ORIGEN_AUTORIZADO
    metodos_permitidos = respuesta.headers.get("access-control-allow-methods", "")
    assert "POST" in metodos_permitidos


def test_peticion_simple_con_origen_autorizado_recibe_allow_origin(monkeypatch) -> None:
    with _crear_cliente_con_origenes(monkeypatch, ORIGEN_AUTORIZADO) as client:
        respuesta = client.get(
            "/api/documents/un-job-inexistente/status",
            headers={"Origin": ORIGEN_AUTORIZADO},
        )

    assert respuesta.headers.get("access-control-allow-origin") == ORIGEN_AUTORIZADO
