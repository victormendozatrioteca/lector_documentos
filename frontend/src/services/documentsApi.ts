/**
 * Cliente de la API del backend (contracts/api.md). Gestiona el
 * `X-Session-Token` para que el backend aplique la regla de un único trabajo
 * activo por sesión (FR-031a).
 *
 * El frontend y el backend se sirven desde orígenes distintos en todo
 * entorno (FR-034, FR-035): toda operación usa una URL base absoluta
 * resuelta desde `VITE_API_BASE_URL` (variable de entorno de compilación),
 * nunca una ruta relativa que asuma mismo origen o un proxy (FR-036). Si la
 * URL base falta o es inválida, o el backend configurado no responde, se
 * traduce a un error comprensible, sin intentar enviar el documento a
 * ningún otro servidor, en particular nunca al que sirve los archivos
 * estáticos del frontend (FR-038).
 */

const RUTA_DOCUMENTOS = '/api/documents'
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

/** Error de configuración (FR-038): la URL base del backend falta o no es
 * una URL absoluta válida. Se detecta antes de invocar ningún endpoint. */
function errorConfiguracionBackend(): ErrorApi {
  return new ErrorApi({
    codigo: 'backend_no_configurado',
    mensaje:
      'No se pudo determinar la dirección del servidor de procesamiento. Contacta con el administrador del sitio.',
  })
}

/** Error de conectividad (FR-038): la URL configurada es válida, pero el
 * backend no respondió (caído, red interrumpida, CORS, etc.). Nunca se
 * recurre al servidor que sirve los archivos estáticos del frontend como
 * alternativa. */
function errorConectividadBackend(): ErrorApi {
  return new ErrorApi({
    codigo: 'backend_no_disponible',
    mensaje:
      'No se pudo conectar con el servidor de procesamiento. Comprueba tu conexión e inténtalo de nuevo.',
  })
}

/** Resuelve la URL base absoluta del backend desde `VITE_API_BASE_URL` en
 * cada llamada (FR-034, FR-035, FR-036). Lanza `ErrorApi` si falta o no es
 * una URL absoluta válida, sin intentar ninguna petición de red. */
function resolverUrlBase(): string {
  const valor = import.meta.env.VITE_API_BASE_URL
  if (!valor || valor.trim() === '') {
    throw errorConfiguracionBackend()
  }
  let url: URL
  try {
    url = new URL(valor)
  } catch {
    throw errorConfiguracionBackend()
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw errorConfiguracionBackend()
  }
  return valor.replace(/\/+$/, '')
}

function construirUrl(ruta: string): string {
  return `${resolverUrlBase()}${ruta}`
}

/** Envuelve `fetch` traduciendo cualquier fallo de red/backend inalcanzable
 * a un error de conectividad comprensible (FR-038). No reintenta ni recurre
 * a ningún otro servidor. */
async function peticion(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch {
    throw errorConectividadBackend()
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

  const respuesta = await peticion(construirUrl(RUTA_DOCUMENTOS), {
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
  const respuesta = await peticion(construirUrl(`${RUTA_DOCUMENTOS}/${jobId}/status`))

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
  return construirUrl(`${RUTA_DOCUMENTOS}/${jobId}/audio`)
}

export async function cancelarDocumento(jobId: string): Promise<void> {
  await peticion(construirUrl(`${RUTA_DOCUMENTOS}/${jobId}`), { method: 'DELETE' })
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
