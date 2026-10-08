"""T047: contract test — un archivo que supera 5.000.000 bytes devuelve 413
con codigo "tamano_excedido" (FR-003)."""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from lector_documentos.main import app
from lector_documentos.models.schemas import TAMANO_MAXIMO_BYTES


def test_post_documents_tamano_excedido_devuelve_413() -> None:
    relleno = "a" * (TAMANO_MAXIMO_BYTES + 1)
    contenido = f"# Título\n\nUn párrafo en español. {relleno}\n"
    with TestClient(app) as client:
        respuesta = client.post(
            "/api/documents",
            files={"file": ("grande.md", io.BytesIO(contenido.encode("utf-8")), "text/markdown")},
        )

    assert respuesta.status_code == 413
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "tamano_excedido"
