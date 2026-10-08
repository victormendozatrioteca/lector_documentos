import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBanner } from '../../src/components/ErrorBanner'

const CASOS: Array<{ codigo: string; mensajeBackend: string }> = [
  { codigo: 'formato_incorrecto', mensajeBackend: 'Solo se admiten archivos Markdown (.md).' },
  {
    codigo: 'tamano_excedido',
    mensajeBackend: 'El archivo supera el tamaño máximo permitido de 5 MB.',
  },
  {
    codigo: 'sin_contenido_narrable',
    mensajeBackend: 'El documento está vacío o no tiene contenido que se pueda narrar.',
  },
  {
    codigo: 'motor_no_disponible',
    mensajeBackend: 'El motor de síntesis de voz no está disponible en este momento.',
  },
  {
    codigo: 'fallo_sintesis',
    mensajeBackend: 'No se pudo generar el audio para este documento.',
  },
]

const PATRONES_TECNICOS = [/traceback/i, /exception/i, /stack/i, /\.py:/i, /\/var\//i, /0x[0-9a-f]+/i]

describe('ErrorBanner (FR-033)', () => {
  it.each(CASOS)(
    'renderiza un mensaje comprensible para el código "$codigo" sin detalles técnicos',
    ({ codigo, mensajeBackend }) => {
      render(<ErrorBanner codigo={codigo} mensaje={mensajeBackend} />)

      const alerta = screen.getByRole('alert')
      expect(alerta.textContent).toBeTruthy()
      for (const patron of PATRONES_TECNICOS) {
        expect(alerta.textContent).not.toMatch(patron)
      }
    }
  )

  it('usa el mensaje del backend cuando el código no se reconoce (sigue siendo comprensible)', () => {
    render(<ErrorBanner codigo="codigo_desconocido_xyz" mensaje="Algo salió mal con tu archivo." />)

    expect(screen.getByRole('alert')).toHaveTextContent('Algo salió mal con tu archivo.')
  })
})
