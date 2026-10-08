import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
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

function configurarAudioElement(): void {
  Object.defineProperty(window.HTMLMediaElement.prototype, 'duration', {
    configurable: true,
    get() {
      return 10
    },
  })
  vi.spyOn(window.HTMLMediaElement.prototype, 'play').mockImplementation(function (
    this: HTMLMediaElement
  ) {
    this.dispatchEvent(new Event('play'))
    return Promise.resolve()
  })
  vi.spyOn(window.HTMLMediaElement.prototype, 'pause').mockImplementation(function (
    this: HTMLMediaElement
  ) {
    this.dispatchEvent(new Event('pause'))
  })
}

describe('AudioPlayer - controles (US2)', () => {
  it('Play/Pausa conserva la posición al reanudar (FR-022)', async () => {
    configurarAudioElement()
    render(<AudioPlayer documento={documentoListo} />)

    const audio = document.querySelector('audio') as HTMLAudioElement
    Object.defineProperty(audio, 'currentTime', { configurable: true, writable: true, value: 4 })

    const boton = screen.getByRole('button', { name: /play/i })
    await userEvent.click(boton)
    const botonPausa = screen.getByRole('button', { name: /pausa/i })
    await userEvent.click(botonPausa)

    expect(audio.currentTime).toBe(4)
  })

  it('Detener regresa la posición al inicio (FR-023)', async () => {
    configurarAudioElement()
    render(<AudioPlayer documento={documentoListo} />)

    const audio = document.querySelector('audio') as HTMLAudioElement
    Object.defineProperty(audio, 'currentTime', { configurable: true, writable: true, value: 7 })

    const botonDetener = screen.getByRole('button', { name: /detener/i })
    await userEvent.click(botonDetener)

    expect(audio.currentTime).toBe(0)
  })

  it('el selector de velocidad aplica playbackRate sin reiniciar la posición (FR-024, FR-025)', async () => {
    configurarAudioElement()
    render(<AudioPlayer documento={documentoListo} />)

    const audio = document.querySelector('audio') as HTMLAudioElement
    Object.defineProperty(audio, 'currentTime', { configurable: true, writable: true, value: 5 })

    const selector = screen.getByLabelText(/velocidad/i) as HTMLSelectElement
    expect(selector.value).toBe('1')

    await userEvent.selectOptions(selector, '1.5')

    expect(audio.playbackRate).toBe(1.5)
    expect(audio.currentTime).toBe(5)
  })

  it('la línea de tiempo muestra el tiempo transcurrido y la duración total (FR-026)', () => {
    configurarAudioElement()
    render(<AudioPlayer documento={documentoListo} />)

    const linea = screen.getByRole('slider', { name: /línea de tiempo|progreso/i })
    expect(linea).toBeInTheDocument()
    expect(linea).toHaveAttribute('max', '10')
  })

  it('permite desplazarse en la línea de tiempo (FR-026)', () => {
    configurarAudioElement()
    render(<AudioPlayer documento={documentoListo} />)

    const audio = document.querySelector('audio') as HTMLAudioElement
    Object.defineProperty(audio, 'currentTime', { configurable: true, writable: true, value: 0 })

    const linea = screen.getByRole('slider', { name: /línea de tiempo|progreso/i })
    fireEvent.input(linea, { target: { value: '6' } })

    expect(audio.currentTime).toBe(6)
  })

  it('los controles permanecen deshabilitados hasta que el audio esté listo (FR-027)', () => {
    render(
      <AudioPlayer
        documento={{
          ...documentoListo,
          estadoProcesamiento: 'procesando',
          duracionSegundos: null,
        }}
      />
    )

    expect(screen.getByRole('button', { name: /play/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /detener/i })).toBeDisabled()
    expect(screen.getByLabelText(/velocidad/i)).toBeDisabled()
    expect(screen.getByRole('slider', { name: /línea de tiempo|progreso/i })).toBeDisabled()
  })
})
