import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AudioPlayer } from '../../src/components/AudioPlayer'
import type { EstadoDocumento } from '../../src/services/documentsApi'

const documentoA: EstadoDocumento = {
  jobId: 'job-a',
  nombreArchivo: 'a.md',
  estadoProcesamiento: 'listo',
  duracionSegundos: 10,
  error: null,
}

const documentoB: EstadoDocumento = {
  jobId: 'job-b',
  nombreArchivo: 'b.md',
  estadoProcesamiento: 'listo',
  duracionSegundos: 8,
  error: null,
}

describe('Single playback guard (FR-028, SC-007)', () => {
  it('reproducir un nuevo documento detiene cualquier otro audio en reproducción', async () => {
    const pauseSpy = vi
      .spyOn(window.HTMLMediaElement.prototype, 'pause')
      .mockImplementation(function (this: HTMLMediaElement) {
        this.dispatchEvent(new Event('pause'))
      })
    vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockImplementation(function (
      this: HTMLMediaElement
    ) {
      this.dispatchEvent(new Event('play'))
      return Promise.resolve()
    })

    render(
      <>
        <AudioPlayer documento={documentoA} />
        <AudioPlayer documento={documentoB} />
      </>
    )

    const botonesPlay = screen.getAllByRole('button', { name: /play/i })

    await userEvent.click(botonesPlay[0])
    await userEvent.click(botonesPlay[1])

    expect(pauseSpy).toHaveBeenCalled()

    const audios = document.querySelectorAll('audio')
    expect(audios[0].paused).toBe(true)
  })
})
