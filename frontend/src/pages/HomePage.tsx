import { useState } from 'react'
import { DocumentUploader } from '../components/DocumentUploader'
import { AudioPlayer } from '../components/AudioPlayer'
import type { EstadoDocumento } from '../services/documentsApi'

/** Página principal: compone el cargador de documentos y el reproductor de audio. */
export function HomePage() {
  const [documentoListo, setDocumentoListo] = useState<EstadoDocumento | null>(null)

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-8 px-4 py-10">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">
          Lector de Documentos con Voz
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Sube un documento Markdown en español y escúchalo narrado con una voz
          generada localmente en el servidor.
        </p>
      </header>

      <DocumentUploader onListo={setDocumentoListo} />

      <AudioPlayer documento={documentoListo} />
    </main>
  )
}
