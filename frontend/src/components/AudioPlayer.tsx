import { useEffect, useRef, useState } from 'react'
import { urlDeAudio, type EstadoDocumento } from '../services/documentsApi'
import { liberarSiActivo, registrarReproduccion } from '../services/playbackGuard'

export interface AudioPlayerProps {
  documento: EstadoDocumento | null
}

const VELOCIDADES = [0.75, 1, 1.25, 1.5, 2] as const
const VELOCIDAD_PREDETERMINADA = 1

function formatearTiempo(segundos: number): string {
  if (!Number.isFinite(segundos) || segundos < 0) return '0:00'
  const minutos = Math.floor(segundos / 60)
  const resto = Math.floor(segundos % 60)
  return `${minutos}:${resto.toString().padStart(2, '0')}`
}

/** Reproductor de audio (T029 base + T032-T037, User Story 1 y 2): carga la
 * fuente solo cuando el documento está `listo`, no reproduce
 * automáticamente (FR-020), Play/Pausa conserva la posición (FR-021,
 * FR-022), Detener regresa al inicio (FR-023), el selector de velocidad
 * aplica `playbackRate` sin regenerar el audio ni reiniciar la posición
 * (FR-024, FR-025), la línea de tiempo permite ver y cambiar la posición
 * (FR-026), los controles están deshabilitados hasta que el audio esté
 * listo y son accesibles por teclado (FR-027), y nunca suenan dos
 * documentos a la vez (FR-028). */
export function AudioPlayer({ documento }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [reproduciendo, setReproduciendo] = useState(false)
  const [velocidad, setVelocidad] = useState<number>(VELOCIDAD_PREDETERMINADA)
  const [tiempoActual, setTiempoActual] = useState(0)
  const [duracion, setDuracion] = useState(0)

  const listo = documento?.estadoProcesamiento === 'listo'
  const src = listo && documento ? urlDeAudio(documento.jobId) : undefined

  useEffect(() => {
    if (!listo) {
      setReproduciendo(false)
      setTiempoActual(0)
      setDuracion(0)
      setVelocidad(VELOCIDAD_PREDETERMINADA)
    }
  }, [listo])

  useEffect(() => {
    const audio = audioRef.current
    return () => {
      if (audio) liberarSiActivo(audio)
    }
  }, [src])

  const alternarReproduccion = (): void => {
    const audio = audioRef.current
    if (!audio) return

    if (audio.paused) {
      registrarReproduccion(audio)
      void audio.play()
      setReproduciendo(true)
    } else {
      audio.pause()
      setReproduciendo(false)
    }
  }

  const detener = (): void => {
    const audio = audioRef.current
    if (!audio) return
    audio.pause()
    audio.currentTime = 0
    setReproduciendo(false)
    setTiempoActual(0)
  }

  const cambiarVelocidad = (nuevaVelocidad: number): void => {
    const audio = audioRef.current
    setVelocidad(nuevaVelocidad)
    if (audio) {
      audio.playbackRate = nuevaVelocidad
    }
  }

  const buscar = (nuevoTiempo: number): void => {
    const audio = audioRef.current
    if (!audio) return
    audio.currentTime = nuevoTiempo
    setTiempoActual(nuevoTiempo)
  }

  const duracionMostrada = duracion || documento?.duracionSegundos || 0

  return (
    <section aria-label="Reproductor de audio" className="rounded-lg border border-slate-200 p-4">
      {src && (
        <audio
          ref={audioRef}
          src={src}
          preload="none"
          onEnded={() => setReproduciendo(false)}
          onPause={() => setReproduciendo(false)}
          onPlay={() => setReproduciendo(true)}
          onLoadedMetadata={(evento) => setDuracion(evento.currentTarget.duration || 0)}
          onDurationChange={(evento) => setDuracion(evento.currentTarget.duration || 0)}
          onTimeUpdate={(evento) => setTiempoActual(evento.currentTarget.currentTime)}
        />
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button type="button" disabled={!listo} onClick={alternarReproduccion}>
          {reproduciendo ? 'Pausa' : 'Play/Pausa'}
        </button>
        <button type="button" disabled={!listo} onClick={detener}>
          Detener
        </button>

        <label className="flex items-center gap-1 text-sm">
          Velocidad
          <select
            aria-label="Velocidad de reproducción"
            disabled={!listo}
            value={velocidad}
            onChange={(evento) => cambiarVelocidad(Number(evento.target.value))}
          >
            {VELOCIDADES.map((v) => (
              <option key={v} value={v}>
                {v}×
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-3 flex items-center gap-2 text-sm text-slate-600">
        <span>{formatearTiempo(tiempoActual)}</span>
        <input
          type="range"
          role="slider"
          aria-label="Línea de tiempo"
          min={0}
          max={duracionMostrada || 0}
          step={0.1}
          value={tiempoActual}
          disabled={!listo}
          onChange={(evento) => buscar(Number(evento.target.value))}
          className="flex-1"
        />
        <span>{formatearTiempo(duracionMostrada)}</span>
      </div>
    </section>
  )
}
