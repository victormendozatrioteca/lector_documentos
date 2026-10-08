"""Integración con Piper (OHF, GPL-3.0), modelo ``es_ES-davefx-medium``
(research.md §2, constitución §2): síntesis 100% local/offline, sin llamadas
a proveedores TTS externos ni fallback automático a otro proveedor (FR-015,
FR-016, FR-017, FR-019).
"""

from __future__ import annotations

import logging
import wave
from collections.abc import Callable
from pathlib import Path

from piper import PiperVoice

logger = logging.getLogger("lector_documentos.tts")

_DIRECTORIO_MODELOS = Path(__file__).resolve().parent.parent.parent.parent / "models"
_RUTA_MODELO = _DIRECTORIO_MODELOS / "es_ES-davefx-medium.onnx"
_RUTA_CONFIG = _DIRECTORIO_MODELOS / "es_ES-davefx-medium.onnx.json"

_voz: PiperVoice | None = None


class MotorNoDisponibleError(Exception):
    """Piper o el modelo de voz no están disponibles en el servidor (HTTP 503)."""


class SintesisFallidaError(Exception):
    """Fallo interno de síntesis no capturado previamente (HTTP 500)."""


class SintesisCanceladaError(Exception):
    """La síntesis se interrumpió por una cancelación cooperativa (FR-031a)."""


def cargar_voz() -> PiperVoice:
    """Carga (una sola vez) y memoiza la voz Piper. Lanza ``MotorNoDisponibleError``
    si el motor o el modelo no pueden cargarse (usado en el chequeo de arranque,
    T010, y en el flujo de síntesis)."""

    global _voz
    if _voz is not None:
        return _voz

    if not _RUTA_MODELO.exists() or not _RUTA_CONFIG.exists():
        raise MotorNoDisponibleError("El modelo de voz Piper no está instalado en el servidor.")

    try:
        _voz = PiperVoice.load(_RUTA_MODELO, config_path=_RUTA_CONFIG)
    except Exception as exc:  # pragma: no cover - depende del entorno
        raise MotorNoDisponibleError(
            "No se pudo cargar el motor de síntesis de voz Piper."
        ) from exc

    return _voz


def verificar_motor_disponible() -> bool:
    """Usado en el startup check de FastAPI (T010) para decidir si el servidor
    puede atender peticiones de síntesis."""

    try:
        cargar_voz()
        return True
    except MotorNoDisponibleError:
        return False


def sintetizar_a_wav(texto: str, ruta_salida: Path) -> float:
    """Sintetiza ``texto`` con Piper y escribe un WAV PCM 16-bit mono a
    22.050 Hz en ``ruta_salida`` (research.md §2). Devuelve la duración en
    segundos. Lanza ``MotorNoDisponibleError`` o ``SintesisFallidaError``."""

    return sintetizar_bloques_a_wav([texto], ruta_salida)


PAUSA_ENTRE_BLOQUES_SEGUNDOS = 0.35
"""Pausa perceptible entre bloques narrables (encabezados, párrafos, citas,
elementos de lista, celdas de tabla) per FR-008/FR-012."""


def sintetizar_bloques_a_wav(
    bloques: list[str],
    ruta_salida: Path,
    debe_cancelar: Callable[[], bool] | None = None,
) -> float:
    """Sintetiza una lista de bloques narrables (markdown_narration.py) como
    un único WAV, insertando una pausa de silencio entre bloques consecutivos
    para respetar el orden y las pausas de FR-008/FR-012. Comprueba
    ``debe_cancelar`` entre bloques para permitir una cancelación cooperativa
    rápida (FR-031a). Devuelve la duración total en segundos."""

    voz = cargar_voz()
    sample_rate = voz.config.sample_rate
    total_muestras = 0

    bloques_no_vacios = [b.strip() for b in bloques if b.strip()]

    try:
        with wave.open(str(ruta_salida), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            muestras_silencio = int(sample_rate * PAUSA_ENTRE_BLOQUES_SEGUNDOS)
            silencio = b"\x00\x00" * muestras_silencio

            for indice, texto in enumerate(bloques_no_vacios):
                if debe_cancelar is not None and debe_cancelar():
                    raise SintesisCanceladaError("Síntesis cancelada por una nueva carga.")
                for chunk in voz.synthesize(texto):
                    if debe_cancelar is not None and debe_cancelar():
                        raise SintesisCanceladaError("Síntesis cancelada por una nueva carga.")
                    wav_file.writeframes(chunk.audio_int16_bytes)
                    total_muestras += len(chunk.audio_int16_array)
                if indice != len(bloques_no_vacios) - 1:
                    wav_file.writeframes(silencio)
                    total_muestras += muestras_silencio
    except (MotorNoDisponibleError, SintesisCanceladaError):
        raise
    except Exception as exc:
        raise SintesisFallidaError("Fallo interno al generar el audio.") from exc

    return total_muestras / sample_rate if sample_rate else 0.0
