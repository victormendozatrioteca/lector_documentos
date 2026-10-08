"""T039: imágenes con texto alternativo narran solo el alt; sin alt no
narran nada (FR-011)."""

from lector_documentos.services.markdown_narration import generar_bloques_narrables


def test_imagen_con_texto_alternativo_narra_solo_el_alt() -> None:
    texto = "![Gráfico de ventas trimestrales](grafico.png)"

    bloques = generar_bloques_narrables(texto)

    assert bloques == ["Gráfico de ventas trimestrales"]


def test_imagen_sin_texto_alternativo_no_narra_nada() -> None:
    texto = "![](grafico.png)"

    bloques = generar_bloques_narrables(texto)

    assert bloques == []


def test_imagen_sin_alt_dentro_de_parrafo_con_texto_no_afecta_al_resto() -> None:
    texto = "Mira este gráfico: ![](grafico.png) que resume el trimestre."

    bloques = generar_bloques_narrables(texto)

    assert len(bloques) == 1
    assert "gráfico.png" not in bloques[0]
    assert "Mira este gráfico" in bloques[0]
    assert "que resume el trimestre" in bloques[0]
