export interface ErrorBannerProps {
  codigo: string
  mensaje: string
}

/** Traduce el `{codigo, mensaje}` del backend (contracts/api.md) a un
 * mensaje comprensible para el usuario, sin exponer detalles técnicos
 * internos (FR-033). Si el código no se reconoce, se usa el `mensaje` que
 * ya envía el backend (también comprensible, nunca técnico). */
const MENSAJES_POR_CODIGO: Record<string, string> = {
  formato_incorrecto: 'Solo se admiten archivos Markdown (.md) codificados en UTF-8.',
  tamano_excedido: 'El archivo supera el tamaño máximo permitido de 5 MB.',
  sin_contenido_narrable:
    'El documento está vacío o no tiene contenido que se pueda narrar.',
  idioma_no_valido: 'El documento no parece contener texto en español.',
  motor_no_disponible:
    'El servicio de generación de voz no está disponible en este momento. Inténtalo más tarde.',
  fallo_sintesis: 'No se pudo generar el audio para este documento. Inténtalo de nuevo.',
  trabajo_no_encontrado: 'El documento solicitado ya no está disponible.',
  audio_no_listo: 'El audio todavía se está generando. Espera unos segundos.',
  error_solicitud: 'La solicitud no pudo procesarse. Revisa el archivo e inténtalo de nuevo.',
  error_interno: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
  error_desconocido: 'Ocurrió un error inesperado. Inténtalo de nuevo.',
}

export function ErrorBanner({ codigo, mensaje }: ErrorBannerProps) {
  const texto = MENSAJES_POR_CODIGO[codigo] ?? mensaje

  return (
    <div
      role="alert"
      className="mt-2 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800"
    >
      {texto}
    </div>
  )
}
