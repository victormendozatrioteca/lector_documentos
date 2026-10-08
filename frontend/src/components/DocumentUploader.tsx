import { useEffect, useRef, useState } from 'react'
import {
  ErrorApi,
  subirDocumento,
  sondearEstado,
  type EstadoDocumento,
} from '../services/documentsApi'
import { ErrorBanner } from './ErrorBanner'

export interface DocumentUploaderProps {
  onListo: (estado: EstadoDocumento | null) => void
}

const ETIQUETAS_ESTADO: Record<string, string> = {
  cargando: 'Cargando documento…',
  procesando: 'Generando audio (procesando)…',
  listo: 'Listo',
  error: 'Error',
  cancelado: 'Cancelado',
}

/** Carga de documento (T027): selector de archivo, nombre/estado y aviso de
 * privacidad (FR-005, FR-029). Usa `sondearEstado` (T028) para reflejar las
 * transiciones cargando→procesando→listo. */
export function DocumentUploader({ onListo }: DocumentUploaderProps) {
  const [nombreArchivo, setNombreArchivo] = useState<string | null>(null)
  const [estado, setEstado] = useState<EstadoDocumento | null>(null)
  const [mensajeError, setMensajeError] = useState<{ codigo: string; mensaje: string } | null>(
    null
  )
  const detenerSondeoRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    return () => {
      detenerSondeoRef.current?.()
    }
  }, [])

  useEffect(() => {
    if (estado?.estadoProcesamiento === 'listo') {
      onListo(estado)
    } else if (estado?.estadoProcesamiento === 'error' || estado?.estadoProcesamiento === 'cancelado') {
      onListo(null)
      if (estado.error) {
        setMensajeError({ codigo: estado.error.codigo, mensaje: estado.error.mensaje })
      }
    }
  }, [estado, onListo])

  const manejarSeleccion = async (evento: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const archivo = evento.target.files?.[0]
    if (!archivo) return

    detenerSondeoRef.current?.()
    onListo(null)
    setNombreArchivo(archivo.name)
    setEstado(null)
    setMensajeError(null)

    try {
      const aceptado = await subirDocumento(archivo)
      setEstado({
        jobId: aceptado.jobId,
        nombreArchivo: aceptado.nombreArchivo,
        estadoProcesamiento: aceptado.estadoProcesamiento,
        duracionSegundos: null,
        error: null,
      })

      detenerSondeoRef.current = sondearEstado(
        aceptado.jobId,
        (nuevoEstado) => setEstado(nuevoEstado),
        (error) => setMensajeError({ codigo: error.codigo, mensaje: error.message })
      )
    } catch (error) {
      setMensajeError(
        error instanceof ErrorApi
          ? { codigo: error.codigo, mensaje: error.message }
          : { codigo: 'error_desconocido', mensaje: 'No se pudo subir el documento.' }
      )
    }

    // Permite volver a seleccionar el mismo archivo tras un error.
    evento.target.value = ''
  }

  const etiquetaEstado = estado ? ETIQUETAS_ESTADO[estado.estadoProcesamiento] : null

  return (
    <section aria-label="Carga de documento" className="rounded-lg border border-slate-200 p-4">
      <label htmlFor="selector-documento" className="block text-sm font-medium text-slate-700">
        Documento Markdown (.md)
      </label>
      <input
        id="selector-documento"
        type="file"
        accept=".md"
        aria-label="Seleccionar documento Markdown"
        onChange={(evento) => void manejarSeleccion(evento)}
        className="mt-2"
      />

      {nombreArchivo && <p className="mt-2 text-sm text-slate-700">{nombreArchivo}</p>}
      {etiquetaEstado && <p className="mt-1 text-sm text-slate-600">{etiquetaEstado}</p>}
      {mensajeError && <ErrorBanner codigo={mensajeError.codigo} mensaje={mensajeError.mensaje} />}

      <p className="mt-4 text-xs text-slate-500">
        El documento se envía al backend (servidor) para procesarlo y generar el
        audio. No se conservan documentos ni audios de forma permanente.
      </p>
    </section>
  )
}
