import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DocumentUploader } from '../../src/components/DocumentUploader'
import type { EstadoDocumento } from '../../src/services/documentsApi'

vi.mock('../../src/services/documentsApi', async () => {
  const actual = await vi.importActual<typeof import('../../src/services/documentsApi')>(
    '../../src/services/documentsApi'
  )
  return {
    ...actual,
    subirDocumento: vi.fn(async (archivo: File) => ({
      jobId: 'job-1',
      sessionToken: 'session-1',
      nombreArchivo: archivo.name,
      estadoProcesamiento: 'cargando' as const,
    })),
    sondearEstado: vi.fn(
      (
        _jobId: string,
        onActualizacion: (estado: EstadoDocumento) => void
      ) => {
        onActualizacion({
          jobId: 'job-1',
          nombreArchivo: 'prueba.md',
          estadoProcesamiento: 'procesando',
          duracionSegundos: null,
          error: null,
        })
        setTimeout(
          () =>
            onActualizacion({
              jobId: 'job-1',
              nombreArchivo: 'prueba.md',
              estadoProcesamiento: 'listo',
              duracionSegundos: 12.5,
              error: null,
            }),
          10
        )
        return () => {}
      }
    ),
  }
})

describe('DocumentUploader', () => {
  beforeEach(() => {
    vi.useRealTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('muestra el nombre del archivo, los estados de carga y el aviso de privacidad (FR-005, FR-029)', async () => {
    const onListo = vi.fn()
    render(<DocumentUploader onListo={onListo} />)

    expect(
      screen.getByText(/se envía al backend|servidor/i)
    ).toBeInTheDocument()

    const archivo = new File(['# Hola\n\nMundo'], 'prueba.md', { type: 'text/markdown' })
    const input = screen.getByLabelText(/seleccionar documento/i) as HTMLInputElement

    await userEvent.upload(input, archivo)

    expect(await screen.findByText('prueba.md')).toBeInTheDocument()
    expect(
      await screen.findByText(/procesando|cargando/i)
    ).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/listo/i)).toBeInTheDocument()
    })
  })
})
