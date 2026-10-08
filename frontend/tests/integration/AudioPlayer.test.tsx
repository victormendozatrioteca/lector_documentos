import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioPlayer } from '../../src/components/AudioPlayer'
import type { EstadoDocumento } from '../../src/services/documentsApi'

const documentoListo: EstadoDocumento = {
  jobId: 'job-1',
  nombreArchivo: 'prueba.md',
  estadoProcesamiento: 'listo',
  duracionSegundos: 10,
  error: null,
}

describe('AudioPlayer', () => {
  it('no reproduce automáticamente; Play requiere una acción explícita del usuario (FR-020, FR-021)', () => {
    const playSpy = vi
      .spyOn(window.HTMLMediaElement.prototype, 'play')
      .mockImplementation(() => Promise.resolve())

    render(<AudioPlayer documento={documentoListo} />)

    expect(playSpy).not.toHaveBeenCalled()
  })

  it('inicia la narración desde el primer bloque al pulsar Play', async () => {
    vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockImplementation(() =>
      Promise.resolve()
    )
    render(<AudioPlayer documento={documentoListo} />)

    const boton = screen.getByRole('button', { name: /play/i })
    await userEvent.click(boton)

    expect(window.HTMLMediaElement.prototype.play).toHaveBeenCalled()
  })

  it('mantiene los controles deshabilitados hasta que el audio esté listo (FR-027)', () => {
    render(
      <AudioPlayer
        documento={{
          ...documentoListo,
          estadoProcesamiento: 'procesando',
          duracionSegundos: null,
        }}
      />
    )

    const boton = screen.getByRole('button', { name: /play/i })
    expect(boton).toBeDisabled()
  })
})
