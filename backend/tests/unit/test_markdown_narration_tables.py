"""T040: las tablas narran encabezados primero, luego las celdas de cada
fila de izquierda a derecha (FR-012)."""

from lector_documentos.services.markdown_narration import generar_bloques_narrables


def test_tabla_narra_encabezados_y_luego_filas_izquierda_a_derecha() -> None:
    texto = "| Nombre | Edad |\n| --- | --- |\n| Ana | 30 |\n| Luis | 25 |\n"

    bloques = generar_bloques_narrables(texto)

    assert bloques == ["Nombre", "Edad", "Ana", "30", "Luis", "25"]
