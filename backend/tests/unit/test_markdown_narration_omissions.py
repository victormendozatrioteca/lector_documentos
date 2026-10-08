"""T041: código en línea, bloques de código, URLs aisladas, líneas
separadoras y HTML crudo se omiten sin ejecutarse ni renderizarse
(FR-013, FR-014)."""

from lector_documentos.services.markdown_narration import generar_bloques_narrables


def test_codigo_en_linea_se_omite() -> None:
    texto = "Ejecuta `rm -rf /` solo si sabes lo que haces."

    bloques = generar_bloques_narrables(texto)

    assert len(bloques) == 1
    assert "rm -rf" not in bloques[0]
    assert "Ejecuta" in bloques[0]


def test_bloque_de_codigo_se_omite_por_completo() -> None:
    texto = (
        "Antes del código.\n\n```python\nimport os\nos.system('rm -rf /')\n```"
        "\n\nDespués del código."
    )

    bloques = generar_bloques_narrables(texto)

    assert bloques == ["Antes del código.", "Después del código."]
    assert not any("os.system" in bloque for bloque in bloques)


def test_url_aislada_se_omite() -> None:
    texto = "https://ejemplo.com/recurso-enlazado"

    bloques = generar_bloques_narrables(texto)

    assert bloques == []


def test_linea_separadora_se_omite() -> None:
    texto = "Primer párrafo.\n\n---\n\nSegundo párrafo."

    bloques = generar_bloques_narrables(texto)

    assert bloques == ["Primer párrafo.", "Segundo párrafo."]


def test_html_crudo_se_omite() -> None:
    texto = "Texto antes.\n\n<div onclick=\"alert('x')\">contenido</div>\n\nTexto después."

    bloques = generar_bloques_narrables(texto)

    assert "Texto antes." in bloques
    assert "Texto después." in bloques
    assert not any("onclick" in bloque or "alert" in bloque for bloque in bloques)
