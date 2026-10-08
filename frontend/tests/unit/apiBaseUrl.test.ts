/**
 * T068: prueba unitaria — el cliente de la API resuelve una URL base
 * absoluta desde `VITE_API_BASE_URL` (vía `import.meta.env`) para cada
 * operación (subida, estado, cancelación, audio), en lugar de la ruta
 * relativa `/api/documents` (FR-034, FR-035, FR-036).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const URL_BASE_BACKEND = 'https://api.ejemplo.test'

describe('Resolución de URL base absoluta (FR-034, FR-035, FR-036)', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubEnv('VITE_API_BASE_URL', URL_BASE_BACKEND)
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            job_id: 'job-1',
            session_token: 'session-1',
            nombre_archivo: 'prueba.md',
            estado_procesamiento: 'cargando',
          }),
          { status: 202 }
        )
      )
    )
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('subirDocumento llama a una URL absoluta construida con VITE_API_BASE_URL', async () => {
    const { subirDocumento } = await import('../../src/services/documentsApi')
    const archivo = new File(['# Título'], 'prueba.md', { type: 'text/markdown' })

    await subirDocumento(archivo)

    const [urlLlamada] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(urlLlamada).toBe(`${URL_BASE_BACKEND}/api/documents`)
  })

  it('consultarEstado llama a una URL absoluta construida con VITE_API_BASE_URL', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            job_id: 'job-1',
            nombre_archivo: 'prueba.md',
            estado_procesamiento: 'procesando',
            duracion_segundos: null,
            error: null,
          }),
          { status: 200 }
        )
      )
    )
    const { consultarEstado } = await import('../../src/services/documentsApi')

    await consultarEstado('job-1')

    const [urlLlamada] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(urlLlamada).toBe(`${URL_BASE_BACKEND}/api/documents/job-1/status`)
  })

  it('cancelarDocumento llama a una URL absoluta construida con VITE_API_BASE_URL', async () => {
    const { cancelarDocumento } = await import('../../src/services/documentsApi')

    await cancelarDocumento('job-1')

    const [urlLlamada] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(urlLlamada).toBe(`${URL_BASE_BACKEND}/api/documents/job-1`)
  })

  it('urlDeAudio devuelve una URL absoluta construida con VITE_API_BASE_URL', async () => {
    const { urlDeAudio } = await import('../../src/services/documentsApi')

    expect(urlDeAudio('job-1')).toBe(`${URL_BASE_BACKEND}/api/documents/job-1/audio`)
  })
})
