let elementoActivo: HTMLAudioElement | null = null

/** Garantiza que no suenen dos documentos simultáneamente (FR-028, SC-007):
 * al iniciar la reproducción de un nuevo elemento de audio, pausa cualquier
 * otro que estuviera sonando. */
export function registrarReproduccion(audio: HTMLAudioElement): void {
  if (elementoActivo && elementoActivo !== audio) {
    elementoActivo.pause()
  }
  elementoActivo = audio
}

/** Libera el registro si el elemento indicado era el activo (p. ej. al
 * desmontar el componente o al pausarlo explícitamente). */
export function liberarSiActivo(audio: HTMLAudioElement): void {
  if (elementoActivo === audio) {
    elementoActivo = null
  }
}
