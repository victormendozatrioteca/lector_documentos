/**
 * Cliente de la API del backend (contracts/api.md). Gestiona el
 * `X-Session-Token` para que el backend aplique la regla de un único trabajo
 * activo por sesión (FR-031a).
 */

const BASE_URL = '/api/documents'
const SESSION_TOKEN_KEY = 'lector_documentos_session_token'

export type EstadoProcesamiento =
  | 'cargando'
  | 'procesando'
  | 'listo'
  | 'error'
  | 'cancelado'

export interface ErrorDetalle {
  codigo: string
  mensaje: string
}

export interface DocumentoAceptado {
  jobId: string
  sessionToken: string
  nombreArchivo: string
  estadoProcesamiento: EstadoProcesamiento
}

export interface EstadoDocumento {
  jobId: string
  nombreArchivo: string
  estadoProcesamiento: EstadoProcesamiento
  duracionSegundos: number | null
  error: ErrorDetalle | null
}

export class ErrorApi extends Error {
  codigo: string

  constructor(detalle: ErrorDetalle) {
    super(detalle.mensaje)
    this.codigo = detalle.codigo
  }
}

export function obtenerSessionToken(): string | null {
  return sessionStorage.getItem(SESSION_TOKEN_KEY)
}

function guardarSessionToken(token: string): void {
  sessionStorage.setItem(SESSION_TOKEN_KEY, token)
}

async function leerError(respuesta: Response): Promise<never> {
  const cuerpo = (await respuesta.json().catch(() => null)) as {
    error?: ErrorDetalle
  } | null
  if (cuerpo?.error) {
    throw new ErrorApi(cuerpo.error)
  }
  throw new ErrorApi({
    codigo: 'error_desconocido',
    mensaje: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
  })
}

export async function subirDocumento(archivo: File): Promise<DocumentoAceptado> {
  const formData = new FormData()
  formData.append('file', archivo)

  const headers: HeadersInit = {}
  const tokenActual = obtenerSessionToken()
  if (tokenActual) {
    headers['X-Session-Token'] = tokenActual
  }

  const respuesta = await fetch(BASE_URL, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!respuesta.ok) {
    await leerError(respuesta)
  }

  const datos = (await respuesta.json()) as {
    job_id: string
    session_token: string
    nombre_archivo: string
    estado_procesamiento: EstadoProcesamiento
  }

  guardarSessionToken(datos.session_token)

  return {
    jobId: datos.job_id,
    sessionToken: datos.session_token,
    nombreArchivo: datos.nombre_archivo,
    estadoProcesamiento: datos.estado_procesamiento,
  }
}

export async function consultarEstado(jobId: string): Promise<EstadoDocumento> {
  const respuesta = await fetch(`${BASE_URL}/${jobId}/status`)

  if (!respuesta.ok) {
    await leerError(respuesta)
  }

  const datos = (await respuesta.json()) as {
    job_id: string
    nombre_archivo: string
    estado_procesamiento: EstadoProcesamiento
    duracion_segundos: number | null
    error: ErrorDetalle | null
  }

  return {
    jobId: datos.job_id,
    nombreArchivo: datos.nombre_archivo,
    estadoProcesamiento: datos.estado_procesamiento,
    duracionSegundos: datos.duracion_segundos,
    error: datos.error,
  }
}

export function urlDeAudio(jobId: string): string {
  return `${BASE_URL}/${jobId}/audio`
}

export async function cancelarDocumento(jobId: string): Promise<void> {
  await fetch(`${BASE_URL}/${jobId}`, { method: 'DELETE' })
}

const INTERVALO_SONDEO_MS = 1500
/** Intervalo de sondeo de estado (~1,5 s, research.md §5). */

export function sondearEstado(
  jobId: string,
  onActualizacion: (estado: EstadoDocumento) => void,
  onError: (error: ErrorApi) => void
): () => void {
  let activo = true

  const consultar = async (): Promise<void> => {
    if (!activo) return
    try {
      const estado = await consultarEstado(jobId)
      if (!activo) return
      onActualizacion(estado)
      if (estado.estadoProcesamiento === 'cargando' || estado.estadoProcesamiento === 'procesando') {
        setTimeout(() => void consultar(), INTERVALO_SONDEO_MS)
      }
    } catch (error) {
      if (!activo) return
      onError(
        error instanceof ErrorApi
          ? error
          : new ErrorApi({
              codigo: 'error_desconocido',
              mensaje: 'No se pudo consultar el estado del documento.',
            })
      )
    }
  }

  void consultar()

  return () => {
    activo = false
  }
}
