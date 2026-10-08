"""T038: los enlaces narran el texto visible, nunca la URL (FR-010)."""

from lector_documentos.services.markdown_narration import generar_bloques_narrables


def test_enlace_narra_solo_el_texto_visible() -> None:
    texto = "Visita [la documentación oficial](https://ejemplo.com/docs) para más detalles."

    bloques = generar_bloques_narrables(texto)

    assert len(bloques) == 1
    assert "la documentación oficial" in bloques[0]
    assert "https://ejemplo.com/docs" not in bloques[0]
    assert "ejemplo.com" not in bloques[0]


def test_varios_enlaces_en_el_mismo_parrafo() -> None:
    texto = "Lee [el primero](https://a.com) y también [el segundo](https://b.com)."

    bloques = generar_bloques_narrables(texto)

    assert len(bloques) == 1
    assert "el primero" in bloques[0]
    assert "el segundo" in bloques[0]
    assert "https://a.com" not in bloques[0]
    assert "https://b.com" not in bloques[0]
