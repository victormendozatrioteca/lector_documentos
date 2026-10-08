/**
 * T069: prueba de integración — cuando `VITE_API_BASE_URL` falta/es
 * inválida, o el backend configurado no responde, la interfaz muestra un
 * error comprensible, nunca un estado de éxito, y nunca envía el documento
 * al servidor propio del frontend (FR-038).
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DocumentUploader } from '../../src/components/DocumentUploader'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

async function subirArchivoDePrueba(): Promise<void> {
  render(<DocumentUploader onListo={vi.fn()} />)
  const archivo = new File(['# Título\n\nContenido en español.'], 'prueba.md', {
    type: 'text/markdown',
  })
  const entrada = screen.getByLabelText('Seleccionar documento Markdown')
  await userEvent.upload(entrada, archivo)
}

describe('Backend ausente/inalcanzable (FR-038)', () => {
  it('muestra un error comprensible y no un éxito cuando VITE_API_BASE_URL falta', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '')
    const fetchEspia = vi.fn()
    vi.stubGlobal('fetch', fetchEspia)

    await subirArchivoDePrueba()

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(screen.queryByText(/listo/i)).not.toBeInTheDocument()
    // Nunca debe intentar enviar el documento a ningún servidor (ni al
    // propio frontend) si la configuración es inválida.
    expect(fetchEspia).not.toHaveBeenCalled()
  })

  it('muestra un error comprensible y no un éxito cuando VITE_API_BASE_URL es inválida', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'no-es-una-url')
    const fetchEspia = vi.fn()
    vi.stubGlobal('fetch', fetchEspia)

    await subirArchivoDePrueba()

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(fetchEspia).not.toHaveBeenCalled()
  })

  it('muestra un error de conectividad comprensible cuando el backend configurado no responde', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'https://backend-caido.ejemplo.test')
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      })
    )

    await subirArchivoDePrueba()

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
    expect(screen.queryByText(/listo/i)).not.toBeInTheDocument()
    const alerta = screen.getByRole('alert')
    expect(alerta.textContent).not.toMatch(/typeerror|failed to fetch|traceback/i)
  })
})
